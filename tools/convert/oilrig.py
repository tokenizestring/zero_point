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
import oilrig_library as library

kit.preview_root = library.preview_root


models = ["jacket", "cellar", "main", "quarters", "helideck", "derrick"]


def makers(name):
    import importlib
    module = importlib.import_module("oilrig_" + name)
    return getattr(module, name), getattr(module, name + "_far")


def main():
    started = time.time()
    os.makedirs(library.preview_root, exist_ok=True)
    if mode == "library":
        library.build(wanted)
    elif mode in ("build", "publish"):
        import oilrig_view
        for name in wanted or models:
            maker, far_maker = makers(name)
            oilrig_view.export(name, maker, far_maker, mode == "publish")
    elif mode == "far":
        import oilrig_view
        for name in wanted or models:
            oilrig_view.export_far(name, makers(name)[1], False)
    elif mode == "preview":
        import oilrig_view
        oilrig_view.preview(wanted, views, samples)
    elif mode == "sheet":
        import oilrig_view
        oilrig_view.sheet(wanted)
    print("DONE", mode, round(time.time() - started, 1), "s", flush=True)


if __name__ == "__main__":
    main()
