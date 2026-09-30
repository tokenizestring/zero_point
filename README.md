# Zero Point

A survival game for Windows, written from scratch in C++20 on Direct3D 11. There is no game engine underneath and no third-party code library: the renderer, netcode, physics, audio mixer, UI and asset baker are all part of this repository.

You wake up on the shore of a large abandoned island with nothing but your hands. Gather, craft, farm, build a base, make junk guns, ride the freight train, and try to stay alive. It is online only: a dedicated server owns the world and every client predicts and mirrors it.

> **Status: early development.** This is a work in progress that changes every day. Expect bugs, crashes, placeholder art, unfinished systems, missing features and saves that break between versions. Nothing here is final.

## Screenshots

![Riding the freight train at sunset](docs/screenshots/train_ride_sunset.jpg)

| | |
|---|---|
| ![The main street of the ruined town](docs/screenshots/village_street.jpg) | ![Inside a fir forest](docs/screenshots/fir_forest.jpg) |
| ![A crafted scrap rifle on the beach](docs/screenshots/scrap_rifle.jpg) | ![Inside a player built base](docs/screenshots/base_interior.jpg) |
| ![The hand drawn island map](docs/screenshots/ink_map.jpg) | ![The view from the summit](docs/screenshots/summit_view.jpg) |
| ![On the flat wagon behind the locomotive](docs/screenshots/train_ride_day.jpg) | ![A railway stop on the north coast](docs/screenshots/railway_stop.jpg) |

The train in these shots is still a set of placeholder boxes. More screenshots will be added as the world fills in.

## What is in the game so far

**World**
- A 9.4 square kilometre island (4608 m terrain, 1 m height samples) shaped by noise and hydraulic erosion, with continuous level of detail
- 13 named places (a ruined town, villages, farms, a harbour, a quarry, a signal post on the summit), roads, and a 10 km closed railway loop
- A freight train on a fixed timetable that you can climb onto, walk around on and ride, and that will kill you if you stand on the track
- Twelve biomes (beach, dunes, marsh, meadow, farmland, woodland, pinewood, heath, moor and more), roads that follow the terrain, and level crossings where they meet the railway
- Bullet holes, blood and footprints that are kept on the server and shown to everyone nearby (the textures for them are still being made)
- Day and night cycle with a procedural sky, weather (overcast, rain, storms with lightning), an ocean you can swim and dive in
- Buildings modelled in Blender with interiors, collision and loot spots

**Survival**
- Health, food, water, breath, body temperature and wetness
- Chopping trees, mining rock and ore, picking plants, looting containers
- Crafting with a recipe list and research, a 30 slot inventory and a hotbar
- Farming with seeds, water and crop growth, campfire cooking, wells
- Base building in four tiers (twig, wood, stone, metal) with doors, code locks, tool cupboards, decay and repair
- Crafted junk guns (pipe pistol, scrap rifle, scrap assault rifle) that jam, misfire and overheat, plus a hunting bow
- A hand-drawn ink map with pins, and a compass

**Multiplayer**
- Dedicated server, server-authoritative movement with client prediction and reconciliation
- Lag compensated hit detection, sleepers, loot bags, persistence of players and the world
- Admin tools: bans, whitelist, password, chat commands

**Technology**
- Deferred renderer: tiled compute lighting, cascaded shadows, ambient occlusion, temporal anti-aliasing, auto exposure, bloom, image based lighting
- GPU skinned characters, instanced foliage with impostors, GPU grass, screen-space reflections on water
- Brush and heightfield collision with swept box traces, moving platforms
- Positional audio on XAudio2 with occlusion, distance delay, echoes, reverb zones and Doppler
- An offline asset baker (texture compression, mesh simplification, terrain generation, font atlases) that packs everything into one file
- Blender Python pipelines that generate guns, trees, grass, buildings and characters

## Numbers

Counted on 30 September 2026. Build output, the portable Blender install and binary assets are not included in these counts.

| Language | Files | Lines |
|---|---:|---:|
| C++ source (.cpp) | 73 | 41,869 |
| C++ headers (.hpp) | 63 | 9,135 |
| HLSL shaders | 18 | 3,753 |
| Python asset tools | 73 | 40,876 |
| Batch | 1 | 135 |
| **Total** | **228** | **95,768** |

| Part of the game | Files | Lines of C++ |
|---|---:|---:|
| Gameplay (`game`) | 38 | 14,741 |
| Renderer (`render`) | 48 | 9,159 |
| Engine core (`core`) | 8 | 8,360 |
| Asset baker (`tools/baker`) | 15 | 7,088 |
| Networking (`net`) | 12 | 6,286 |
| Interface (`ui`) | 6 | 3,522 |
| Audio (`audio`) | 2 | 1,112 |
| Utilities (`utils`) | 4 | 588 |

Other numbers: 276 texture sets, 180 sounds, 13 landmarks, 10 km of railway, 8 roads and tracks, 60 Hz simulation, up to 500 players per server.

## Building

Requirements:
- Windows 10 or 11, 64 bit
- Visual Studio 2022 with the C++ desktop workload (the script finds the compiler by itself)
- Git LFS, because textures, models and sounds are stored with it

```
git lfs install
git clone https://github.com/tokenizestring/zero_point.git
cd zero_point
build.bat
```

`build.bat` compiles the asset baker, bakes `assets` into `build\bin\zero_point.pak`, compiles the shaders and links the game and the server. The first bake takes a few minutes.

- `build.bat code` rebuilds only the code and shaders
- `build.bat terrain` rebuilds only the terrain cache and writes a preview image
- `build.bat debug` makes a debug build

## Running

Start a server, then the game:

```
build\bin\zero_point_server.exe --name "My island"
build\bin\zero_point.exe
```

Choose Play and pick the server from the browser, or join directly with `zero_point.exe --connect 127.0.0.1`.

Default keys: WASD to move, Shift to sprint, C to crouch, Space to jump, Tab for the inventory, M for the map, E to use, R to reload, I to inspect the held gun. Keys can be changed in the settings.

## Repository layout

| Folder | Contents |
|---|---|
| `core` | Application loop, platform layer, maths, and `engine.hpp` with every constant and data structure |
| `render` | Direct3D 11 renderer, terrain, water, foliage, characters, sky, post processing |
| `game` | Movement, survival, harvesting, building, farming, weapons, the train, maps |
| `net` | Transport, server, client, persistence, admin tools |
| `ui` | Menus, HUD, the ink map |
| `audio` | The mixer |
| `shaders` | HLSL |
| `tools/baker` | The offline asset baker |
| `tools/convert` | Blender and Python scripts that generate or convert assets |
| `assets/raw` | Everything the baker reads: textures, models, characters, animations, sounds, skies |
| `assets/source` | Inputs for the generator scripts |

The generator scripts expect a portable Blender 4.5 in `tools/blender`. It is not part of the repository.

## Roadmap

See [roadmap.md](roadmap.md). Next up: biomes with their own ground and plants, sea cliffs, animals and fish, real train and station models, new player characters.

## Credits

Third-party assets and their licences are listed in [CREDITS.md](CREDITS.md).
