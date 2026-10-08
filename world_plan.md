# World plan: Jersey at 5x

The island grows from 4.6 km across (9.4 square km of land) to a 10.24 km map with about 45 square km of land, modelled on the real island of Jersey at roughly 0.62 scale: about 9 km east to west and 5.6 km north to south. Real geography gives every part of the map its own character, real towns to plan street by street, and real landmarks to turn into monuments.

## Shape and terrain

- A tilted plateau: high cliffs along the whole north coast (100 to 130 m), sloping gently down to a low south coast with wide sandy bays.
- Deep wooded valleys running north to south off the plateau (St Peter's Valley, Waterworks Valley, Grands Vaux, Queen's Valley), each with a stream, ponds and a reservoir in two of them.
- The west coast is one long surf beach (St Ouen's Bay) backed by a sea wall, dunes, marsh and a freshwater pond.
- The south-east corner runs out into a huge rocky tidal reef (La Rocque) that dries at low tide.
- Headlands with fortifications at every corner: Grosnez (north-west), Corbière (south-west), Noirmont (south), La Hougue (south-east), St Catherine and Mont Orgueil (east).

## Biomes

| Biome | Where | Ground | Plants |
|---|---|---|---|
| Cliff heath | North coast plateau edge | Thin turf, rock, heather | Gorse, heather, bracken, wind-bent hawthorn |
| Dunes | Les Quennevais and behind St Ouen's Bay | Sand, marram | Marram, sea holly, burnet rose, pine shelterbelts |
| Wetland | St Ouen's Pond, Grouville marsh | Mud, reeds, standing water | Reeds, willow, alder, yellow iris |
| Farmland | The central plateau | Ploughed soil, potato côtils on steep south slopes, pasture | Hedgerows, field oaks, cider orchards |
| Wooded valleys | North to south valleys | Leaf litter, ferns, moss | Oak, beech, sycamore, holly, ivy, ferns |
| Rocky shore | La Rocque, east coast | Rock, weed, shingle | Seaweed, lichen |
| Urban | St Helier, St Aubin, Gorey | Tarmac, cobbles, flags | Street trees, overgrowth in ruins |

## Towns and villages

Every town is planned street by street: an organic street plan following the terrain, no grids, every house from the unique house set (bld_home_01 to 24 and more to come), shops with their own names, back gardens, alleys, walls and overgrowth.

| Place | Kind | What is there |
|---|---|---|
| St Helier | Capital town | Harbour and docks with cranes and containers, marina, Royal Square, King Street shops, Central Market, fish market, hospital, parish hall, churches, flats, car parks, Fort Regent on the hill |
| St Aubin | Harbour town | Steep streets, harbour, St Aubin's Fort on a tidal islet, the old railway station |
| Gorey | Harbour village | Harbour below Mont Orgueil castle, pubs, fishermen's cottages |
| St Brelade's Bay | Resort | Seafront hotels, beach cafés, church by the sand |
| Les Quennevais | Estate | 1960s housing estate, school, sports centre, shopping parade |
| St Ouen | Parish village | Church, parish hall, farms, the manor |
| St Peter | Parish village | Church, pub, garage, close to the airport |
| St Lawrence | Parish village | Church, close to the war tunnels |
| St Mary | Parish village | Church, pub, farms |
| St John | Parish village | Church, recreation ground, near the quarry |
| Trinity | Parish village | Church, manor, the zoo |
| St Martin | Parish village | Church, public hall |
| Rozel | Fishing hamlet | Tiny harbour, cottages, a barracks |
| Grouville | Parish village | Church, common with a golf course |
| St Clement | Coastal estates | Bungalows, sea wall |
| St Saviour | Parish village | Church, hospital grounds, the old school |

## Monuments

Each monument has a loot tier (1 basic to 3 elite), a hazard and something to do.

| Monument | Tier | Hazard | What to do |
|---|---|---|---|
| War tunnels (underground hospital) | 3 | Dark, flooded galleries, scavengers | Power the tunnels with fuses, red keycard vault |
| Airport | 3 | Open ground, snipers on the control tower | Hangars, terminal, a cargo plane wreck, blue keycard room |
| Power station and fuel farm | 3 | Fire, explosions, toxic smoke | Restart the turbine hall, red keycard control room |
| Harbour and docks | 2 | Scavenger crews | Cranes to climb, container yard, ship wreck alongside |
| Mont Orgueil castle | 2 | Heights | Climb the keep, hidden rooms |
| Elizabeth Castle | 2 | Cut off by the tide | Reach it over the causeway at low tide |
| Corbière lighthouse | 2 | Cut off by the tide | Lamp room, radio |
| Noirmont battery | 2 | Bunkers and tunnels | Gun emplacements, observation tower, green keycard bunker |
| Les Landes and Grosnez | 2 | Exposed clifftop | Racecourse stands, observation tower, castle ruins |
| Plémont holiday camp | 1 | Collapsing buildings | Chalets, ballroom, cliff caves below |
| Ronez quarry | 2 | Drops and machinery | Crusher plant, conveyors, explosives store |
| Reservoirs and dams | 1 | Deep water | Pump houses, water treatment, the dam walkway |
| Zoo | 2 | Escaped animals | Enclosures, vet clinic |
| Radio mast at Les Platons | 2 | Heights | Climb the mast, transmitter hall |
| Hospital | 2 | Scavengers | Medical loot, morgue, generator |
| La Hougue Bie | 1 | Dark | Neolithic tomb under a chapel mound, bunker beside it |
| Desalination plant | 1 | Machinery | Pump hall, tanks |
| Offshore oil rig | 3 | Scavengers, heights | Built: six decks, helideck, 47 loot spots |

## Roads and rail

- Main roads follow the real A roads out of St Helier to each parish, with narrow banked green lanes between fields.
- The railway follows the two historic lines: the Jersey Railway along St Aubin's Bay to Corbière, and the Jersey Eastern Railway from St Helier to Gorey, with the old stations at St Aubin, Millbrook, La Haule and Gorey.

## What is still missing compared with Rust

1. Monument puzzles: keycards (green, blue, red), fuse boxes, levers, locked doors, vault rooms.
2. Locked crates that take time to open and call scavengers when they do.
3. Hostile scavengers guarding monuments, roaming patrols, an armed helicopter patrol and an armoured car.
4. Safe trading towns with traders, vending machines and a recycler.
5. Airdrops from a cargo plane, a cargo ship event.
6. Boats (rowing boat, motor boat) and fishing, diving for loot.
7. Research and blueprints, a deeper crafting tree, workbench tiers.
8. Electricity: generators, solar panels, batteries, lights, alarms, turrets, traps.
9. More animals: wolves, foxes, rabbits, chickens, Jersey cows and feral dogs.
10. Clothing and armour crafted from hide and cloth.
11. Caves, mines and the tunnel network.
12. Teams, map markers and team chat.

## Technical work for 10.24 km

1. Terrain heights at 2 m spacing (5121 by 5121) instead of 1 m: one spacing constant shared by the C++ and every shader that assumes 1 m (terrain, grass, water, rain), CDLOD at 40 patch cells by 2^7 with 8 levels, splat and shading maps at 4 m.
2. Baker terrain generator rewritten around the Jersey outline, plateau, valleys and bays, with the cache version bumped.
3. Network positions widened beyond the current 16 bit limit (about 2.7 km either way at 1/12 m), the interest grid enlarged from 80 to 160 cells of 64 m, protocol version bumped.
4. Static world geometry split into cells and culled by distance, foliage limits raised, buildings as instanced species with far models.
5. Spawn search, harvest node indexing and save versions updated.
6. Dedicated server memory and CPU kept low: heights stored as 16 bit, far herds and nodes updated rarely, nothing render-only on the server.

## Order of work

1. Road and pavement surfaces, decay decals and street dressing (in progress).
2. Technical groundwork for the 10.24 km map.
3. New terrain: outline, plateau, valleys, bays, biomes.
4. Roads and rail across the new island.
5. St Helier, St Aubin and Gorey planned street by street, then the parish villages.
6. Monuments one by one, each with its puzzle and loot tier.
7. Gameplay systems from the missing list, in the order above.
