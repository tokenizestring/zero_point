order = ["oak", "birch", "pine", "hawthorn", "willow", "gorse", "bramble", "heather", "bracken", "reed", "rush", "marram", "foxglove", "cowparsley", "daisy", "buttercup", "poppy", "bluebell", "thistle", "wrack", "mushroom"]

budgets = {
    "tree": {"": (9000, 20000), "_far": (1500, 3500), "_shadow": (400, 1500), "_impostor": (2, 2)},
    "shrub": {"": (1500, 4000), "_far": (300, 700)},
    "small": {"": (80, 600)},
}

base = {"tree": (-1.0, 0.1), "shrub": (-0.35, 0.05), "small": (-0.2, 0.05)}

species = {
    "oak": {"kind": "tree", "variants": 3, "height": (6.8, 16.0), "sway": 0.08, "near": 45.0, "impostor": 110.0, "far": 1100.0, "shadow": 170.0, "block": True, "biomes": ["broadleaf woodland", "farmland", "meadow"]},
    "birch": {"kind": "tree", "variants": 3, "height": (9.0, 13.0), "sway": 0.14, "near": 45.0, "impostor": 110.0, "far": 1100.0, "shadow": 170.0, "block": True, "biomes": ["broadleaf woodland", "moorland", "coastal heath", "pinewood"]},
    "pine": {"kind": "tree", "variants": 3, "height": (12.0, 18.0), "sway": 0.1, "near": 45.0, "impostor": 110.0, "far": 1100.0, "shadow": 170.0, "block": True, "biomes": ["pinewood", "coastal heath", "dunes"]},
    "hawthorn": {"kind": "tree", "variants": 3, "height": (3.0, 5.0), "sway": 0.03, "near": 35.0, "impostor": 90.0, "far": 800.0, "shadow": 120.0, "block": True, "trunk": [0.16, 0.13, 0.15], "notes": "windswept: trunk and crown lean along model +X (engine +X before instance yaw); align +X with the downwind direction; variant 1 carries white blossom", "biomes": ["coastal heath", "farmland", "meadow", "moorland", "dunes"]},
    "willow": {"kind": "tree", "variants": 3, "height": (7.0, 10.0), "sway": 0.12, "near": 45.0, "impostor": 110.0, "far": 1000.0, "shadow": 160.0, "block": True, "trunk": [0.52, 0.63, 1.16], "notes": "multi-stemmed from a low fork; trunk_radius is the radius enclosing every stem at 1.3 m; variant 2 has one stem leaning hard along model +X, point +X at open water", "biomes": ["marsh", "meadow"]},
    "gorse": {"kind": "shrub", "variants": 3, "height": (1.0, 2.0), "sway": 0.02, "near": 28.0, "far": 260.0, "shadow": 60.0, "block": True, "biomes": ["coastal heath", "moorland", "dunes", "farmland"]},
    "bramble": {"kind": "shrub", "variants": 3, "height": (1.0, 1.6), "across": (2.0, 3.0), "sway": 0.03, "near": 26.0, "far": 220.0, "shadow": 50.0, "block": True, "biomes": ["broadleaf woodland", "farmland", "coastal heath", "meadow"]},
    "heather": {"kind": "shrub", "variants": 3, "height": (0.3, 0.5), "across": (0.6, 1.2), "sway": 0.008, "near": 18.0, "far": 140.0, "shadow": 30.0, "block": False, "biomes": ["coastal heath", "moorland", "summit"]},
    "bracken": {"kind": "shrub", "variants": 3, "height": (0.8, 1.3), "sway": 0.07, "near": 22.0, "far": 160.0, "shadow": 40.0, "block": False, "biomes": ["moorland", "coastal heath", "broadleaf woodland", "pinewood"]},
    "reed": {"kind": "shrub", "variants": 3, "height": (1.8, 2.4), "sway": 0.16, "near": 26.0, "far": 240.0, "shadow": 50.0, "block": False, "biomes": ["marsh"]},
    "rush": {"kind": "small", "variants": 3, "height": (0.5, 0.8), "sway": 0.05, "far": 90.0, "shadow": 28.0, "block": False, "biomes": ["marsh", "moorland", "meadow"]},
    "marram": {"kind": "small", "variants": 3, "height": (0.6, 1.0), "sway": 0.09, "far": 110.0, "shadow": 30.0, "block": False, "biomes": ["dunes", "beach"]},
    "foxglove": {"kind": "small", "variants": 3, "height": (1.0, 1.5), "sway": 0.08, "far": 90.0, "shadow": 28.0, "block": False, "biomes": ["broadleaf woodland", "pinewood", "coastal heath", "farmland"]},
    "cowparsley": {"kind": "small", "variants": 3, "height": (0.8, 1.1), "sway": 0.07, "far": 80.0, "shadow": 25.0, "block": False, "biomes": ["farmland", "meadow", "broadleaf woodland"]},
    "daisy": {"kind": "small", "variants": 3, "height": (0.4, 0.6), "sway": 0.05, "far": 70.0, "shadow": 22.0, "block": False, "biomes": ["meadow", "farmland"]},
    "buttercup": {"kind": "small", "variants": 3, "height": (0.3, 0.5), "sway": 0.04, "far": 65.0, "shadow": 20.0, "block": False, "biomes": ["meadow", "farmland", "marsh"]},
    "poppy": {"kind": "small", "variants": 3, "height": (0.4, 0.6), "sway": 0.055, "far": 75.0, "shadow": 22.0, "block": False, "biomes": ["farmland", "meadow"]},
    "bluebell": {"kind": "small", "variants": 3, "height": (0.25, 0.35), "sway": 0.025, "far": 60.0, "shadow": 18.0, "block": False, "biomes": ["broadleaf woodland"]},
    "thistle": {"kind": "small", "variants": 3, "height": (0.8, 1.2), "sway": 0.04, "far": 85.0, "shadow": 26.0, "block": False, "biomes": ["meadow", "farmland", "dunes", "coastal heath"]},
    "wrack": {"kind": "small", "variants": 2, "height": (0.03, 0.3), "across": (0.5, 1.2), "sway": 0.0, "far": 70.0, "shadow": 0.0, "block": False, "biomes": ["rocky shore", "beach"]},
    "mushroom": {"kind": "small", "variants": 2, "height": (0.05, 0.16), "sway": 0.0, "far": 40.0, "shadow": 12.0, "block": False, "biomes": ["broadleaf woodland", "pinewood"]},
}


def suffixes(kind):
    return {"tree": ("", "_far", "_shadow", "_impostor"), "shrub": ("", "_far"), "small": ("",)}[kind]


def model_name(name, variant, suffix=""):
    return "flora_%s_%d%s" % (name, variant, suffix)
