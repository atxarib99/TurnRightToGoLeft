# acmock User Guide

## What is acmock?

**acmock** lets you test Assetto Corsa apps without launching the game. Your app runs in a web browser with simulated car telemetry, so you can catch bugs and preview layouts instantly.

## Installation

No installation needed. You just need:
- Python 3.8 or later (runs on your desktop Python, not the AC embedded interpreter)
- The code from this repository

## Quick Start

From the repo root, run:

```sh
python -m tools.acmock.run /path/to/your/app/app.py
```

Then open the URL printed to your console (usually `http://localhost:8765`) in any web browser. You'll see the app running with fake car data.

## Common Commands

### Preview an app
```sh
python -m tools.acmock.run /path/to/your/app/app.py
```
Opens the app with built-in synthetic telemetry.

### Play back real session data
```sh
python -m tools.acmock.run /path/to/your/app/app.py \
    --csv tools/acmock/sample_data/lap.csv --loop
```
Replays a recorded lap CSV file, looping it forever. Great for testing app behavior across a full session.

### Test without a browser
```sh
python -m tools.acmock.run /path/to/your/app/app.py --headless --frames 3
```
Renders 3 frames and prints the raw scene data as JSON. Useful for automated testing.

### Generate sample data
```sh
python -m tools.acmock.run --dump-csv my_lap.csv
```
Creates a CSV file of synthetic telemetry you can edit and reuse.

## Options

| Option | What it does |
|---|---|
| `<app.py>` | Path to the app to test |
| `--csv PATH` | Play back a CSV file instead of synthetic data |
| `--loop` | Loop the data forever |
| `--fps N` | Frames per second (default 30) |
| `--port N` | HTTP port (default 8765) |
| `--scenario {idle,driving,trail-brake,pit}` | Type of synthetic data to use |
| `--strict` | Warn about unmapped car state identifiers |
| `--headless` | Run without a browser, print JSON |
| `--dump-csv PATH` | Generate a CSV and exit |

## In the Browser

Once your app is running:

- **Canvas** — Shows your app window exactly as it would appear in-game
- **Console** — Displays `ac.log()` output and any Python errors
- **Controls** — Live sliders to adjust car state (speed, throttle, etc.)

Click and drag sliders to test your app's response to changing values in real time.

## Tips

- **Start simple** — Try an app you didn't write first to get comfortable with the tool
- **Test edge cases** — Use sliders to push your app to extreme values (0 speed, full throttle, damage) and watch for crashes
- **Use a CSV** — Record a real lap from the game, export it as CSV, and replay it. This finds bugs that synthetic data misses
- **Check the console** — Python errors appear there, not in your terminal

## Limitations

- **Not physics-accurate** — acmock uses fake telemetry, so don't trust the exact numbers
- **No in-game features** — Special AC features (car damage files, physics data) may not be available, but the app will still run and show what it can
- **Fonts are approximate** — The browser canvas rendering isn't pixel-perfect like the game

## Next Steps

- Read `python/BUILDING_APPS.md` to understand how AC apps work
- Edit `tools/acmock/sample_data/lap.csv` to create test scenarios
- Look at the `--strict` flag if your app uses car state identifiers acmock doesn't recognize
