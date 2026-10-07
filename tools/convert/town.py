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
    return {
        "terrace": (town_terrace.terrace, town_terrace.terrace_far, None),
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
