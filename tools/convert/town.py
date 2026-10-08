import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
mode = arguments[0] if arguments else "library"
wanted = [name for name in (arguments[1].split(",") if len(arguments) > 1 else []) if name]
samples = int(arguments[2]) if len(arguments) > 2 else 48
views = [name for name in (arguments[3].split(",") if len(arguments) > 3 else []) if name]

import buildkit as kit
import town_library

kit.preview_root = os.path.join(kit.root, "assets", "previews", "town")


def registry():
    import town_terrace
    import town_shop
    import town_pub
    return {
        "terrace": (town_terrace.terrace, town_terrace.terrace_far, None),
        "shop": (town_shop.shop, town_shop.shop_far, None),
        "pub": (town_pub.pub, town_pub.pub_far, None),
    }


specs = {
    "terrace": {
        "shots": {
            "street": ((-5.5, -13.0, 1.7), (0.2, -4.5, 3.2), 26.0),
            "door": ((3.0, -8.0, 1.65), (0.6, -4.5, 1.6), 38.0),
            "yard": ((4.2, 11.5, 4.2), (-0.2, 5.4, 1.2), 30.0),
            "row": ((9.0, -14.0, 5.0), (0.0, 0.0, 3.5), 30.0),
        },
        "rooms": {
            "hall": ((1.25, -3.85, 1.6), (1.55, 0.4, 1.3), 17.0),
            "parlour": ((-0.7, -4.6, 1.65), (-1.2, 0.4, 1.0), 16.0),
            "parlour_back": ((-0.25, 0.25, 1.6), (-1.3, -4.6, 1.1), 17.0),
            "kitchen": ((1.4, 1.0, 1.6), (-1.9, 3.7, 0.9), 16.0),
            "kitchen_back": ((-1.65, 3.95, 1.65), (1.8, 0.9, 0.9), 16.0),
            "front_bed": ((-0.35, -0.75, 4.75), (-2.2, -3.9, 4.0), 16.0),
            "back_bed": ((0.1, 4.0, 4.7), (-2.2, 0.0, 3.9), 16.0),
            "box_room": ((0.6, -2.25, 4.7), (2.3, -4.0, 3.8), 16.0),
            "bathroom": ((1.7, 1.8, 4.75), (0.6, 4.0, 3.8), 16.0),
            "landing": ((0.9, -1.85, 4.7), (1.6, 1.4, 3.9), 18.0),
        },
        "levels": [("GROUND", 2.6, -0.4, 2.7), ("UPPER", 5.4, 2.8, 5.6), ("ROOF", 11.0, 5.6, 11.0)],
        "margin": 0.06,
    },
    "shop": {
        "shots": {
            "street": ((-6.0, -14.0, 1.7), (0.4, -5.0, 3.0), 26.0),
            "shopfront": ((2.2, -9.5, 1.7), (0.2, -5.0, 2.2), 30.0),
            "rear": ((5.5, 12.0, 4.0), (0.0, 4.5, 2.5), 28.0),
        },
        "rooms": {
            "shop": ((-1.6, -4.0, 1.65), (2.0, 0.6, 1.0), 16.0),
            "counter": ((2.5, 0.75, 1.75), (-1.5, -4.0, 1.0), 16.0),
            "storeroom": ((2.6, 3.9, 1.75), (-1.6, 1.8, 0.7), 16.0),
            "stair": ((-0.4, 3.6, 1.7), (-2.8, 0.8, 2.6), 18.0),
            "lounge": ((2.75, -4.3, 5.25), (-2.5, -1.5, 4.4), 16.0),
            "lounge_back": ((-2.6, -4.2, 5.2), (2.5, -1.6, 4.3), 16.0),
            "kitchenette": ((0.2, 0.4, 5.2), (-2.8, 4.2, 4.3), 16.0),
            "bedroom": ((2.75, 1.0, 5.3), (1.0, 4.3, 4.0), 16.0),
            "corridor": ((2.9, -0.5, 5.2), (-3.0, -0.4, 4.6), 18.0),
        },
        "levels": [("GROUND", 3.2, -0.4, 3.3), ("UPPER", 5.9, 3.4, 6.0), ("ROOF", 12.5, 6.0, 12.5)],
        "margin": 0.06,
    },
    "pub": {
        "shots": {
            "street": ((-9.5, -18.0, 1.7), (0.0, -5.5, 3.6), 24.0),
            "frontage": ((3.6, -11.5, 1.7), (-0.6, -5.5, 2.6), 28.0),
            "corner": ((-12.0, -10.0, 2.2), (-5.0, -2.0, 3.6), 26.0),
            "rear": ((9.0, 16.0, 4.5), (0.0, 5.5, 3.0), 26.0),
        },
        "rooms": {
            "bar": ((4.6, -4.5, 1.65), (-1.0, 0.3, 1.1), 16.0),
            "fireside": ((-0.4, -4.6, 1.65), (-5.0, -1.8, 0.9), 16.0),
            "servery": ((2.75, 0.45, 1.7), (-2.5, -3.6, 1.1), 16.0),
            "darts": ((2.2, -3.7, 1.6), (5.2, 0.8, 1.5), 18.0),
            "store": ((1.0, 1.55, 1.7), (5.0, 4.6, 0.5), 16.0),
            "passage": ((-3.65, 1.45, 1.65), (-3.6, 5.0, 1.0), 20.0),
            "gents": ((-2.55, 3.4, 1.6), (-0.5, 4.95, 0.8), 16.0),
            "ladies": ((-1.5, 2.75, 1.6), (-0.2, 1.35, 0.8), 16.0),
            "stair": ((-4.95, 0.2, 1.7), (-4.95, 4.6, 3.4), 18.0),
            "living": ((0.2, -0.6, 5.0), (-4.6, -3.0, 4.1), 16.0),
            "bedroom": ((5.0, -4.55, 5.0), (1.2, -1.0, 4.1), 16.0),
            "bathroom": ((-0.95, 1.65, 5.0), (-2.6, 4.6, 4.0), 16.0),
            "bed2": ((2.1, 1.75, 5.0), (-0.3, 4.6, 4.0), 16.0),
            "kitchen": ((3.3, 1.65, 5.0), (5.3, 3.8, 4.1), 16.0),
            "corridor": ((5.3, 0.65, 5.0), (-5.0, 0.65, 4.6), 18.0),
            "landing": ((-3.6, 0.5, 5.1), (-4.0, 4.8, 3.9), 18.0),
        },
        "levels": [("GROUND", 3.0, -0.4, 3.1), ("UPPER", 5.7, 3.2, 5.9), ("ROOF", 12.0, 5.9, 12.0)],
        "margin": 0.06,
    },
}


def main():
    started = time.time()
    os.makedirs(kit.preview_root, exist_ok=True)
    if mode == "library":
        town_library.build(wanted)
        kit.write_sheet()
    elif mode == "build":
        import town_view
        table = registry()
        for name in wanted or list(table):
            maker, far_maker, hero = table[name]
            town_view.export(name, maker, far_maker, hero)
    elif mode == "preview":
        import town_view
        for name in wanted or list(specs):
            town_view.preview(name, specs[name], views, samples)
    elif mode == "sheet":
        import town_view
        town_view.sheet(wanted or list(specs), {})
    print("DONE", mode, round(time.time() - started, 1), "s", flush=True)


if __name__ == "__main__":
    main()
