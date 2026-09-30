# Zero Point roadmap

The target is a Rust-grade island survival game. You wake up on the shore with nothing but your hands, then gather, craft, build, hunt and survive on a big, detailed, abandoned island.

Every step works the same way: build, capture, inspect every shot up close, fix, and repeat. A box only gets ticked once it holds up in close-up captures.

## Phase 1: Hands and first person

1. [x] Spawn with nothing (bare hands only)
2. [x] Two-handed boxer guard with IK arms, both fists on screen
3. [x] Virtual forearm twist bones (no candy-wrapper wrists)
4. [ ] Tight fist: fingers rest on the palm with no clipping, thumb wraps over the index and middle fingers, fingers held together
5. [ ] Skin texture: no grainy noise, natural tone, fine pores, knuckle creases, nails, subtle dirt in the creases only
6. [ ] Skin lighting: soft subsurface look (light bleeding at the edges, warm shadow edge), gentle sheen
7. [ ] Smooth hand silhouette: rounded fingers and knuckles, no faceted edges
8. [ ] Idle life: breathing, micro drift, occasional fist re-clench, weight shift
9. [ ] Movement: step bob in sync with footsteps, strafe lean, sprint arm pump, jump tuck, landing dip, lower guard when crouched
10. [ ] Look lag: hands trail camera turns and settle with a slight overshoot
11. [ ] Punches: alternating jab and cross, shoulder turn, fist rotation, snap at full extension, camera kick
12. [ ] Punch impacts: per-surface sound and shake, knuckle scrapes and self-damage when punching rock or bark
13. [ ] Bare-hand interactions: reach-and-grab pickups, cupped hands to drink water
14. [ ] Equip transitions between fists and tools (hands drop, tool rises)
15. [ ] Tool holds rebuilt around the new hands (rock, stone hatchet, spear, torch)

## Phase 1b: Crafted guns

- [x] New gun construction kit in Blender (bolts, welds, hose clamps, springs, carved wood) with baked worn textures
- [x] Pipe pistol rebuilt (couplings, stitch welds, hose clamps, painted bolted frame, walnut grip, burlap wrap)
- [x] In-game gun viewer: press I to bring the held gun up, drag to turn it
- [x] Test loadout: spawn with the pipe pistol, scrap rifle and ammo (remove once testing is done)
- [x] Scrap rifle rebuilt to the same standard (ported receiver, bolt with ball knob, scope on welded rail, drilled brake, walnut stock with laced cheek pad), left hand now rests on the forend wrap
- [x] Scrap AR: box-tube receiver in red-oxide primer, drilled heat-shield handguard on hose clamps, peep sight, curved taped magazine, wooden charging knob; full-auto with a real magazine swap and charging-handle rack
- [x] Junk-gun behaviour: jams that get worse with heat and wear (R clears them), duds and hangfires, uneven fire rate with stutters, bloom, barrel smoke when hot, jittery recoil, wear per shot
- [ ] Support hand: tighter finger wrap on the rifle forend
- [ ] Hunting bow and arrows rebuilt
- [ ] Stone hatchet and stone pickaxe rebuilt

## Phase 2: Trees, chopping and gathering

16. [x] Real trees: continuous trunk (no segment cracks), root flare, bark detail, dense branch sprays, LODs
    - [x] Six Blender-built firs with near, far, impostor (8-view billboard) and shadow-proxy LODs, dithered crossfades
    - [x] Dead snags rebuilt in Blender (drooping dead branches, forked twigs, broken tops)
17. [ ] Wind: trunk sway, branch flutter, needle shimmer
18. [ ] Chopping: a notch that deepens with every hit (visible wedge), bark and wood chips, the whole tree shakes
19. [ ] Felling: creak, lean, fall pivoting on the notch, ground impact and bounce, branches snap off
    - [x] Trees creak, topple away from whoever chopped them (same direction for every player), crash down in a burst of dust, then sink away
    - [ ] Bounce, branches snapping off
20. [ ] Stump and log stay behind; the log chops down into wood and the branches give sticks
21. [ ] Rocks: chips fly, the rock cracks and shrinks, ore nodes show veins
22. [ ] Ground pickups with their own models: sticks, stones, flint, fibre plants, mushrooms, berries
23. [ ] Stone hatchet and stone pickaxe modelled in Blender (lashed handles) with proper swing animations

## Phase 3: Rendering quality to Rust level

24. [ ] Terrain: height-blended layers, macro variation, detail normals, parallax, triplanar cliffs, wet beach band, footprints in sand
25. [x] Grass: denser, mixed species, translucency, wind waves, bends around the player, no pop-in
26. [x] Ocean: layered detail normals, screen-space reflections, crest glow, rolling surf bands with lace foam, wet sand, see-through shallows, sun glitter, no dark horizon bands
    - [x] Underwater: fog and absorption, moving caustics on the seabed, Snell's window when looking up, half-submerged lens at the surface, muffled sound and an underwater hum
    - [x] Swimming: wading slows you down, swim and dive (look down or hold C, space to rise), buoyancy with wave bob, breaststroke hands, breath bar and drowning, splash and stroke sounds
    - [x] Twilight and night no longer go black (sky multiple scattering, more exposure headroom)
    - [ ] Sunrise and sunset colour balance (less red wash)
    - [ ] Rivers and ponds
27. [ ] Sky: volumetric clouds, sun shafts, fog layers, rain and storms, moonlit nights
    - [x] Rain and storms: server-driven weather phases, streaks that stop under roofs, wet surfaces, grey overcast sky and reflections, heavier fog, lightning flashes with delayed thunder, rain ambience muffled indoors
    - [x] Cloud layer thickens and darkens with the weather; splashes where rain lands; day and night clock matches the sun
    - [x] Branching lightning bolts on the horizon, hidden behind terrain and trees, synced with the flash and thunder
    - [x] Sun shafts through the canopy (quarter-res sky mask, radial blur toward the sun, fades with cloud cover)
    - [ ] Volumetric clouds, puddle ripples
28. [ ] Lighting: contact shadows, better ambient occlusion, specular occlusion, interior light probes, shadowed local lights
29. [ ] Post: time-of-day colour grading, lens effects, subtle grain, optional motion blur
30. [ ] Materials pass: every surface checked (albedo range, roughness, normal strength), grime, moss and leak decals
31. [ ] Performance: LODs everywhere, occlusion culling, streaming, 60+ fps at 1440p ultra
    - [x] GPU pass profiler, reduced-resolution outer shadow cascades, shadow proxies, rock and snag far LODs (forest 34 ms → 13 ms)
    - [x] Shadow cascades scissored to their used area and the near cascade capped at 2048 (forest evening 12.8 ms → 8.6 ms at 1600x900)

## Phase 4: The island

32. [ ] Map redesign: biomes (beaches, pine forest, meadows, rocky highlands, marsh, cliffs), rivers, lakes, caves
    - [x] Island enlarged to 4.6 km across (9.4 square km of land) with mountains, highlands and 13 named places
    - [x] Biome map baked from height, slope, coast distance, wind exposure and wetness: beach, rocky shore, dunes, marsh, meadow, farmland with field plots, broadleaf woodland, pinewood, coastal heath, moorland, summit
    - [x] 16 ground layers (compressed), grass density and height, planting and ambience all driven by the biome
    - [x] Raised sea cliffs on stretches of the coast that are clear of roads and rails
    - [ ] Own ground texture for every biome layer (needles, heath, moor, marsh, dune, shingle, turf, soil)
    - [ ] Plants per biome: oak, birch, Scots pine, hawthorn, willow, gorse, bramble, heather, bracken, reeds, marram, wildflowers
    - [ ] Hedgerows along field borders, rivers, lakes, caves
33. [ ] Roads and paths, bridges, fences, power poles, an old rail line
    - [x] Five roads and a 10 km railway loop graded into the terrain, drawn on the map
    - [x] Freight train on a fixed timetable with five stops: you can climb on, walk around and ride it, it kills you on the track, and everyone sees riders locked to the wagons
    - [x] Train sounds: engine, wheel roar, rail joints, two-tone horn, brake squeal, all with distance delay, occlusion and Doppler
    - [x] Detailed track panels bent along the line; locomotive and flat wagon models
    - [ ] Remaining wagons and the coach, spinning wheels, stations and platforms at the stops
34. [ ] Detailed, fully furnished structures (Blender-built or CC0 downloads):
    - [x] Cottage, two-storey house, ruin, shed and barn built in Blender with interiors, collision and loot spots; town, villages, farms and hamlets placed across the island
    - [ ] Fisherman's cottages (kitchen, table, beds, shelves, stove, clutter)
    - [ ] Farmhouse, barn, silo and sheds
    - [ ] Village: church, pub, shop and houses in different states of ruin
    - [ ] Lighthouse with spiral stairs and lamp room
    - [ ] Radio station on the hill
    - [ ] Harbour with piers, boats and warehouses
    - [ ] Military bunker and abandoned research site
35. [ ] Interiors: furniture, props, debris, broken windows, doors that open, lootable cupboards and drawers
36. [ ] Monuments with loot tiers and hazards
37. [ ] Scattered points of interest: campsites, wrecks, cabins, caves
38. [ ] Ambient life: birds, gulls, fish, insects

## Phase 5: Survival mechanics

39. [ ] Vitals: hunger, thirst, temperature (clothes, fire, wetness), stamina, bleeding, broken bones, sickness from bad water or raw meat
40. [ ] Crafting tree: hands, then stone, bone, wood, copper and iron (furnace), gunpowder, junk guns; workbench levels 1 to 3
41. [ ] Crafting UI: recipe book, queue, blueprints found in the world
42. [ ] Cooking: campfire, drying rack, boiling water
43. [ ] Animals: deer, boar, wolf, bear, chicken, rabbit, with AI, hunting and skinning (meat, hide, bone, fat)
    - [ ] Rigged and animated models: red deer, wild boar, Jersey cow, wolf, fox, rabbit (in progress), then birds, fish and crabs
    - [ ] Server-simulated herds and packs by biome, replication, hit detection, carcass harvesting
44. [ ] Clothing crafted from hide and cloth, with warmth and protection
45. [ ] Building: foundations, walls, doors, windows, roofs and stairs; twig, wood, stone and metal tiers; decay; locks
    - [x] Wood, stone and metal tiers (hammer upgrade with RMB, LMB repair, stone and metal shrug off bullets)
    - [x] Tool cupboard: building privilege within 25 m, doors open only for authorized players
    - [x] Decay outside cupboard range (wood 3 h, stone 5 h, metal 8 h)
    - [x] Gable roofs that keep the rain out, twig tier (cheap stick lattice, 30 hp, decays in an hour), per-tier hit sounds and surfaces
    - [ ] Detailed Blender models for every tier and piece (kit loader ready: `structures` model, parts `<tier>_<piece>`)
    - [x] Code locks: craft from 100 metal fragments, fit to a door you can open, 4-digit keypad, wrong guesses shock you (1 s cooldown), a lock overrides cupboard access, re-keying (hold sprint + E) locks everyone else out; saved with the world
46. [x] Storage, furnace smelting, fuel
47. [ ] Farming polish
48. [ ] Combat: fists, clubs, spears (throwable), bows, crossbow, junk guns, hit reactions, ragdolls, hostile scavenger AI
49. [x] Death and respawn: dropped bag, sleeping bags, beach respawn
50. [x] Save and load for the world and the player
51. [x] Weather that matters: rain soaks you, nights get cold, storms
    - [x] Server-side wetness and body temperature: rain and swimming soak you, roofs keep you dry, campfires, furnaces and torches warm you and dry you off
    - [x] Cold burns food faster and freezing hurts (death by the cold); heat burns water faster; Cold, Freezing, Overheating and Wet on the HUD
    - [x] Server console `weather <clear|overcast|rainy|stormy>` and `--weather N`

## Phase 6: Audio and UI polish

52. [ ] Footsteps per surface, cloth rustle, sprint breathing, heartbeat when hurt
    - [x] Footstep sound follows the ground layer you stand on
    - [x] Positional sound realism: walls and hills muffle sounds, sounds behind you are duller, bullets crack and whiz past, ricochets, and other players hear your reloads, bolt work, swings and hits
53. [ ] Ambience layers per biome and weather, music stingers
    - [x] Birdsong, crickets and wind scale with the biome (loud woods, quiet windy moor)
54. [ ] UI: inventory drag and drop, crafting menu, map markers, notes, tooltips, death screen
    - [x] Item icon atlas pipeline (baker stage `item_icons` from `assets/raw/icons/<item>.png`, text fallback); server browser password field and lock marker
    - [x] Death screen: how you died (or who killed you), where your things are, the real respawn key
    - [ ] Render the item icons, map markers
55. [x] Settings: key rebinding, graphics presets, audio sliders
    - [x] Key rebinding page (17 actions, click and press, defaults, saved in settings.ini); picture presets
    - [x] Separate effects and ambience volume sliders under the master volume

## Phase 7: Multiplayer (online only)

56. [x] Authoritative dedicated server, player sync, world state sync
    - [x] zero_point_server.exe, 500 slots, server browser, host a local server from the menu
    - [x] Movement rewritten and simulated on the server; client prediction with zero corrections
    - [x] Guns, recoil, spread, jams and ammo on the server; lag-compensated hits; gunshots heard up to 900 m
    - [x] Inventory, crafting, vitals, harvesting, building, containers, farming, arrows on the server
    - [x] World saves, returning players restored, sleepers that can be killed and looted, death bags
    - [x] Chat, name tags, hit direction, kill feed
    - [ ] Third-person held items and animations for other players (after the new player models)
    - [ ] Voice proximity chat
    - [x] Server admin tools: bans, whitelist, admins with chat commands, password, `zero_point_admin.cfg`
    - [x] Names belong to the first identity key that uses them (no more logging in as someone else); `forget <name>` frees one
    - [x] Server and client clocks in double precision (the old clock stopped after about nine hours of uptime); commands carry an exact timestamp
    - [x] Moving platforms in the shared movement code (the train), predicted with zero corrections
    - [ ] Remote console
