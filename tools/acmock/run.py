"""CLI entry point: run an unmodified AC app under the mocks.

    python -m tools.acmock.run python/slipometer/slipometer.py
    python -m tools.acmock.run python/fuel_tracker/fuel_tracker.py --csv tools/acmock/sample_data/lap.csv --loop
    python -m tools.acmock.run --dump-csv tools/acmock/sample_data/lap.csv
    python -m tools.acmock.run python/iamspeedKMH/iamspeedKMH.py --headless --frames 3

The runner injects the mocks into sys.modules BEFORE importing the app (some apps
call ac.* at import time), then drives acMain once and acUpdate/onFormRender per
frame, serving the resulting scene to the browser (or printing it in --headless).
"""

import argparse
import importlib.util
import os
import sys
import time
import traceback
import types

from . import data_provider, mock_ac, mock_acsys, mock_sim_info


def install_mocks(rt):
    """Register the mock modules so the app's imports resolve to them."""
    sys.modules["ac"] = mock_ac
    sys.modules["acsys"] = mock_acsys

    # third_party.sim_info interception: a stand-in package + the fake submodule,
    # plus a bare 'sim_info' alias (the real module documents that import form).
    tp = types.ModuleType("third_party")
    tp.__path__ = []                      # mark as a package (single-process: no bleed)
    tp.sim_info = mock_sim_info
    sys.modules["third_party"] = tp
    sys.modules["third_party.sim_info"] = mock_sim_info
    sys.modules["sim_info"] = mock_sim_info

    # popUpAirBrake imports directkeys, whose real module calls ctypes.WinDLL at
    # import time and crashes off-Windows. Stub it with no-ops.
    dk = types.ModuleType("directkeys")
    dk.PressKey = lambda *a, **k: None
    dk.ReleaseKey = lambda *a, **k: None
    sys.modules["directkeys"] = dk

    mock_ac.bind(rt)


def load_app(app_path):
    app_path = os.path.abspath(app_path)
    app_dir = os.path.dirname(app_path)
    sys.path.insert(0, app_dir)
    try:
        os.chdir(app_dir)                 # parity with AC running from the app dir
    except OSError:
        pass
    modname = "ac_app_" + os.path.splitext(os.path.basename(app_path))[0]
    spec = importlib.util.spec_from_file_location(modname, app_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)          # may run ac.* at import; mocks are live
    return mod


def safe_call(rt, label, fn):
    """Run an app callback; route any exception to the console pane, keep going."""
    try:
        fn()
        return True
    except Exception:
        tb = traceback.format_exc()
        for line in ("!! %s raised:" % label, tb.rstrip()):
            for sub in line.splitlines():
                rt.log_line(sub)
        return False


def build_runtime(args):
    if args.csv:
        provider = data_provider.DataProvider(
            mode="csv", csv_path=args.csv, loop=args.loop, scenario=args.scenario)
    else:
        provider = data_provider.DataProvider(
            mode="synthetic", loop=args.loop, scenario=args.scenario)
    return mock_ac.Runtime(provider, strict=args.strict)


def drive_once(rt, mod, dt, elapsed, server=None):
    """Advance one frame: events -> data -> acUpdate -> onFormRender -> scene."""
    if server is not None:
        for ev in server.drain_events():
            safe_call(rt, "event", lambda ev=ev: rt.dispatch_event(ev))
    rt.data.update(elapsed)
    rt.reset_frame()
    ac_update = getattr(mod, "acUpdate", None)
    if ac_update is not None:
        safe_call(rt, "acUpdate", lambda: ac_update(dt))
    if rt.render_callback is not None:
        safe_call(rt, "onFormRender", lambda: rt.render_callback(dt))
    return rt.scene()


def run_headless(rt, mod, frames):
    import json
    safe_call(rt, "acMain", lambda: mod.acMain("1.0"))
    dt = 1.0 / 30.0
    scene = None
    for i in range(frames):
        scene = drive_once(rt, mod, dt, dt * (i + 1))
    print(json.dumps(scene, indent=2, default=str))
    return scene


def run_server(rt, mod, args):
    from . import server as server_mod
    safe_call(rt, "acMain", lambda: mod.acMain("1.0"))
    server_mod.serve(rt, mod, drive_once, fps=args.fps, port=args.port)


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m tools.acmock.run")
    p.add_argument("app", nargs="?", help="path to the app .py file")
    p.add_argument("--csv", help="telemetry CSV to play back")
    p.add_argument("--loop", action="store_true", help="loop CSV / lap")
    p.add_argument("--fps", type=int, default=30, help="frames per second (default 30)")
    p.add_argument("--port", type=int, default=8765, help="HTTP port (default 8765)")
    p.add_argument("--scenario", default="driving",
                   choices=["idle", "driving", "trail-brake", "pit"],
                   help="synthetic scenario")
    p.add_argument("--strict", action="store_true",
                   help="warn when getCarState hits an unmapped identifier")
    p.add_argument("--headless", action="store_true",
                   help="render N frames and print the scene JSON, no server")
    p.add_argument("--frames", type=int, default=3, help="frames for --headless")
    p.add_argument("--dump-csv", metavar="PATH",
                   help="write a synthetic-lap CSV to PATH and exit")
    args = p.parse_args(argv)

    if args.dump_csv:
        path = os.path.abspath(args.dump_csv)
        d = os.path.dirname(path)
        if d and not os.path.isdir(d):
            os.makedirs(d)
        out, n = data_provider.dump_csv(path, scenario=args.scenario)
        print("Wrote %d rows to %s" % (n, out))
        return 0

    if not args.app:
        p.error("an app path is required (or use --dump-csv)")

    rt = build_runtime(args)
    install_mocks(rt)
    mod = load_app(args.app)

    if args.headless:
        run_headless(rt, mod, args.frames)
    else:
        run_server(rt, mod, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
