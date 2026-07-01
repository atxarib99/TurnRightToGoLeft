# acmock — preview & test AC apps without the game

Assetto Corsa apps can't normally run outside the game: AC injects the built-in
`ac` and `acsys` modules and the apps read shared memory through
`third_party/sim_info.py`. **acmock** mocks all of that, runs an *unmodified* app,
and renders its UI in your browser — driven by built-in synthetic telemetry or by
**playing back a CSV** of session data.

It's a **layout + behaviour preview**, not a physics-accurate simulator: enough to
catch UI layout mistakes, label/format bugs, lap/session-reset logic errors, and
crashes *before* you copy the app into the game.

> Lives in `tools/` (outside `python/`) on purpose — the release workflow zips
> `python/`, so dev tooling here never ships to users. acmock runs on your normal
> desktop Python (3.8+) and uses **stdlib only — no pip, no `python3-tk`**. (The
> apps themselves still must stay Python-3.3 compatible for the game; acmock
> doesn't change that.)

## Quick start

From the repo root:

```sh
# Preview an app with built-in synthetic telemetry, then open the printed URL
python -m tools.acmock.run python/slipometer/slipometer.py
#   -> acmock: serving 'slipometer' at http://localhost:8765

# Generate a sample telemetry CSV (already committed at sample_data/lap.csv)
python -m tools.acmock.run --dump-csv tools/acmock/sample_data/lap.csv

# Play that CSV back, looping
python -m tools.acmock.run python/fuel_tracker/fuel_tracker.py \
    --csv tools/acmock/sample_data/lap.csv --loop

# Smoke-test without a browser: print the rendered scene as JSON
python -m tools.acmock.run python/iamspeedKMH/iamspeedKMH.py --headless --frames 3
```

Open the URL in any browser. You'll see the app window rendered on a canvas
(drawn rectangles + labels), live control widgets you can interact with, and a
console pane showing `ac.log` / `ac.console` output and any tracebacks.

## CLI

| flag | meaning |
|---|---|
| `<app.py>` | path to the app to run (positional) |
| `--csv PATH` | play back a telemetry CSV instead of synthetic data |
| `--loop` | loop the CSV / synthetic lap |
| `--fps N` | frames per second (default 30) |
| `--port N` | HTTP port (default 8765) |
| `--scenario {idle,driving,trail-brake,pit}` | synthetic data preset |
| `--strict` | warn in the console when `getCarState` hits an unmapped identifier |
| `--headless [--frames N]` | render N frames and print scene JSON, no server |
| `--dump-csv PATH` | write a synthetic-lap CSV to PATH and exit |

## How it works

- `sys.modules['ac']` / `['acsys']` are replaced with mocks before the app is
  imported (some apps call `ac.*` at import time).
- `acsys.CS.<Name>` resolves to the string `"<Name>"`; the mock `ac.getCarState`
  returns the **correct shape** per identifier (scalar / 2-tuple `RideHeight` /
  3-tuple vectors / 4-tuple per-wheel) from `arity.py`, so positional unpacks like
  `fl,fr,rl,rr = ac.getCarState(0, acsys.CS.SlipRatio)` don't crash.
- `ac` drawing is recorded into a per-frame *scene*: `glColor3f` sets the current
  colour, `glQuad` appends a filled rect (negative width/height normalised), and
  labels/controls are tracked persistently. The scene is streamed to the browser
  over Server-Sent Events and drawn on an HTML5 canvas.
- `third_party.sim_info` is intercepted with a fake `SimInfo` backed by the same
  data source, so the real `mmap` shared-memory reader never loads.
- `acMain` / `acUpdate` / `onFormRender` are each wrapped so an exception shows a
  traceback in the console pane instead of killing the harness. Apps that read the
  game's car-data files (`scrubometer`, `liftLag`) or a cwd-relative config
  (`button_box`) therefore still render — they just log the missing-file error.
- Any `ac.*` function not explicitly implemented becomes a logging no-op, so apps
  using rarely-used APIs never `AttributeError`.

## CSV schema

One row per sample; the same row feeds both `getCarState` and `sim_info`. All
columns are optional — missing ones fall back to defaults.

| column | meaning |
|---|---|
| `t` | sample time in seconds (drives wall-clock playback) |
| `SpeedKMH`, `Gas`, `Brake`, `LapCount`, `RPM`, `ERSMaxJ`, … | `getCarState` scalars (column = identifier name) |
| `SlipRatio_FL` / `_FR` / `_RL` / `_RR` | per-wheel 4-tuple |
| `RideHeight_F`, `RideHeight_R` | 2-tuple |
| `AccG_X` / `_Y` / `_Z` | 3-tuple |
| `physics.fuel`, `physics.tc`, `physics.abs`, … | `sim_info.physics.*` |
| `physics.carDamage0`..`4`, `physics.tyreWear0`..`3` | array elements |
| `graphics.session`, `graphics.sessionTimeLeft`, `graphics.bestTime` (string `M:SS:mmm`), `graphics.tyreCompound` | `sim_info.graphics.*` |
| `static.maxRpm`, `static.track` (string), `static.playerNick`, … | `sim_info.static.*` |
| `carName`, `tyreCompound`, `inPit` | misc `ac.getCarName` / `getCarTyreCompound` / `isCarInPit` |

`sample_data/lap.csv` is a generated example you can open, edit, or regenerate
with `--dump-csv`.

## Limitations

- Canvas fonts/metrics are approximate — this is a layout preview, not pixel-exact.
- The `getCarState` shape table is exact for identifiers the repo's apps use;
  the broader set is best-effort from `ACPythonDocumentation.pdf`. Run with
  `--strict` to surface any identifier acmock had no data for.
- `--car-data` (pointing `scrubometer`/`liftLag` at real `tyres.ini`/`.lut`
  files), live in-game recording, and headless PNG screenshots are noted as
  future enhancements, not in this version.

## Tip: IDE autocomplete

For editor autocomplete on `ac`, the third-party stubs package
[`ac-stubs`](https://pypi.org/project/ac-stubs/) (`pip install ac-stubs` in your
dev environment only) provides type hints. It's purely an IDE aid — it can't run
or render apps; that's what acmock is for.
