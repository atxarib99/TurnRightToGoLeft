# Building Assetto Corsa Apps

A practical guide for writing new apps in this repo. It combines the official AC
Python API (`ACPythonDocumentation.pdf` in the repo root) with the patterns the
existing apps in `python/` already use. Read this before starting a new app — it
will save you from rediscovering the quirks.

> Scope note: this guide documents how things work today. It does not propose
> changes to existing apps. When you build something new, copy the conventions
> below so it fits in.

---

## 1. What an Assetto Corsa app actually is

An AC app is a folder of Python that AC loads at runtime. AC ships an **embedded
Python interpreter** and exposes two built-in modules to your script:

- **`ac`** — the UI + telemetry API (create windows, labels, buttons; draw
  shapes; read `getCarState(...)`). Documented in `ACPythonDocumentation.pdf`.
- **`acsys`** — an enum module holding the constants you pass to
  `ac.getCarState`, e.g. `acsys.CS.SpeedKMH`.

Neither module exists outside the game, so **you cannot run an app from a normal
terminal** — there is no local execution and no unit test harness. You test by
copying the app into AC and watching the in-game log/console. Treat the game as
your only runtime.

### ⚠️ The interpreter: Python 3.3, and **no pip — ever**

AC's embedded interpreter is **Python 3.3** and it is sealed:

- **There is no `pip`.** You cannot install third-party packages for an app to
  use. `pip install <anything>` is not an option at any point — not during
  development, not at the user's machine. The interpreter is exactly what AC
  ships and nothing more.
- **Only the Python 3.3 standard library plus AC's built-in `ac`/`acsys` are
  available.** Even parts of the stdlib that rely on C-extension binaries
  (`ctypes`, `mmap`, etc.) may not be on `sys.path` by default — see the lib-dir
  bootstrap in §4.
- **If your app needs external code, you must *vendor* it** — copy the pure-Python
  source into the app's own folder (the way `third_party/sim_info.py` and
  `popUpAirBrake/directkeys.py` are vendored) so it ships inside the release zip.
  A vendored dependency must itself be importable under Python 3.3 with no native
  build step.
- **Write Python 3.3-compatible code.** No f-strings (3.6+), no `pathlib` niceties
  you'd expect from later versions, no walrus operator, no `async`/`await` syntax
  you might reach for. The existing apps use `"...".format(...)` and string
  concatenation — match that. When unsure whether a language feature or stdlib API
  exists, assume 3.3 and check.

### Where apps install

In a real AC install, each app lives at:

```
…/steamapps/common/assettocorsa/apps/python/<app_name>/<app_name>.py
```

You enable it in-game under **Options → General → UI Modules**, then drag it onto
the screen from the right-hand app sidebar.

Several apps in this repo hardcode that Steam path when they read car data files
(see `scrubometer.py:89` and `liftLag.py:7`). That's the canonical install
location.

### How this repo maps to that

```
python/
  <app_name>/
    <app_name>.py          # the app; entry module, MUST match folder name
    README.md              # one-paragraph description + usage
    third_party/           # vendored helpers (only if needed)
      sim_info.py          # shared-memory reader (see §4)
    <whatever>.config      # optional runtime config the app reads
static/                    # screenshots/gifs for the README gallery (not shipped)
```

The release workflow (`.github/workflows/release.yml`) simply zips the entire
`python/` directory into `TurnRightToGoLeft-latest.zip` and publishes it as the
`latest` GitHub release. Users unzip that into their AC `apps/python/` folder.
**Consequence:** the folder name, the `.py` filename, and the string passed to
`ac.newApp(...)` should all line up, and anything your app needs at runtime must
live inside the app folder so it survives the zip.

---

## 2. The app lifecycle

Every app is built around three functions AC calls for you. The `template/`
app is the minimal skeleton (`python/template/template.py`):

```python
import sys
import ac
import acsys

appName = "template"

def acMain(ac_version):
    appWindow = ac.newApp(appName)      # create the window, get its id
    ac.setSize(appWindow, 100, 100)     # width, height in px
    ac.addRenderCallback(appWindow, onFormRender)  # register draw callback
    return appName                      # MUST return the app name string

def acUpdate(deltaT):                   # called every physics tick
    pass

def onFormRender(deltaT):               # called every frame, after acUpdate
    pass
```

| Function | When it runs | Use it for |
|---|---|---|
| `acMain(ac_version)` | Once, when the app loads | Create the window and all controls, set positions/sizes, load config/car-data files, register callbacks. **Must return the app name string.** |
| `acUpdate(deltaT)` | Every physics update | Read telemetry, do calculations, update state. `deltaT` is seconds since last call. |
| `onFormRender(deltaT)` | Every rendered frame | Push values to labels (`ac.setText`) and draw shapes (`ac.glQuad`). **All custom drawing must happen here** — drawing only works inside the render callback. |

Critical rules learned from the existing apps:

- **`acMain` must `return appName`** (a string). Returning nothing breaks the app.
- **Register the render callback** with `ac.addRenderCallback(appWindow, onFormRender)`,
  otherwise `onFormRender` is never called and nothing draws.
- **Drawing (`ac.glQuad`, `ac.glColor3f`, …) only works from inside the render
  callback.** Doing it in `acUpdate` does nothing.
- **`acUpdate` vs `onFormRender` split:** every app here computes/aggregates in
  `acUpdate` and only *displays* in `onFormRender`. Follow that. Putting heavy
  work in the render path costs frames.
- Module-level code runs at import, *before* `acMain`. Be careful calling `ac.*`
  at module scope — `state_of_kachow.py:42` calls `ac.getCarState(...)` at import
  time to read `ERSMaxJ`, which works but is fragile (it runs before a car may be
  fully ready). Prefer doing setup inside `acMain`.

---

## 3. Reading telemetry: `ac.getCarState`

`ac.getCarState(carId, infoIdentifier [, wheelIdentifier])` is the primary
telemetry call. `carId` is `0` for the player's car (always 0 in these apps).
The identifier comes from `acsys.CS.*`.

```python
brake = ac.getCarState(0, acsys.CS.Brake)            # scalar 0..1
speed = ac.getCarState(0, acsys.CS.SpeedKMH)         # scalar km/h
fl, fr, rl, rr = ac.getCarState(0, acsys.CS.SlipRatio)   # 4-tuple per wheel
```

### Return shapes

`getCarState` returns one of three shapes depending on the identifier:

- **Scalar** — most pedal/speed/lap values.
- **3D vector** `(x, y, z)` — accelerations, velocities, world position.
- **4D / per-wheel** `(FL, FR, RL, RR)` — anything tyre-related (slip, camber,
  temps, load). Note the wheel order used throughout this repo is **FL, FR, RL,
  RR** (see `slipometer.py:104`, `scrubometer.py:197`).

On failure `getCarState` returns `0`. There's no exception — guard against zero
where it matters.

### Commonly useful `acsys.CS` identifiers

Pulled from the PDF; the ones the repo actually uses are marked ✓.

**Scalars**
- `SpeedMS`, `SpeedMPH`, `SpeedKMH` ✓ — speed in m/s, mph, km/h
- `Gas` ✓, `Brake` ✓, `Clutch` — pedal inputs `[0,1]`
- `Gear` — `0..max` (0 is reverse/neutral depending on car)
- `RPM` — engine rpm
- `Steer` — steering in radians `[-2π, 2π]`
- `LapCount` ✓ — current session lap count (key for per-lap logic)
- `LapTime`, `LastLap`, `BestLap` — times in **milliseconds**
- `LapInvalidated` — `{0,1}` did you cut the lap
- `NormalizedSplinePosition` — `[0,1]` position around the lap
- `PerformanceMeter` — seconds delta vs your best lap
- `RideHeight` ✓ — *returns a 2-tuple* `[front, rear]` (see `liftLag.py:100`)
- `TurboBoost`, `CGHeight`, `DriveTrainSpeed`, `IsEngineLimiterOn`
- KERS/ERS (only meaningful on cars with ERS):
  `KersCharge` ✓, `KersInput` ✓, `ERSRecovery` ✓, `ERSDelivery` ✓,
  `ERSHeatCharging` ✓, `ERSCurrentKJ` ✓, `ERSMaxJ` ✓ (in Joules — divide by
  1e6 for MJ)

**3D vectors** `(x, y, z)`
- `AccG` — g-forces on the car's CG
- `Velocity`, `LocalVelocity`, `LocalAngularVelocity`
- `SpeedTotal` — `(kmh, mph, ms)`
- `WorldPosition` — car coordinates on the map
- `WheelAngularSpeed`

**4D / per-wheel** `(FL, FR, RL, RR)`
- `SlipAngle` ✓ — degrees, angle between intended and actual direction
- `SlipRatio` ✓ — longitudinal slip
- `CamberRad` / `CamberDeg`
- `Load` — vertical load per tyre
- `CurrentTyresCoreTemp`, `ThermalState` — tyre temps °C
- `DynamicPressure` — tyre pressure psi
- `TyreRadius`, `TyreLoadedRadius`, `SuspensionTravel`, `TyreDirtyLevel`
- `Mz`, `NdSlip`, `TyreSlip`, `Dy`

**With a wheel identifier** (3rd arg `acsys.CS.FL/FR/RL/RR`) — returns a 3D vector
for that wheel: `TyreContactNormal`, `TyreContactPoint`, `TyreHeadingVector`,
`TyreRightVector`. Example from the PDF: `ac.getCarState(0, TyreContactPoint, FR)`.

**Aero** (3rd arg is an index): `Aero` with `o=0` drag coeff, `o=1` front lift,
`o=2` rear lift.

### General info functions (not via getCarState)

- `ac.getCarName(0)` ✓ — car folder name (e.g. `ks_lamborghini_huracan_gt3`),
  used to locate the car's data files (`liftLag.py:61`, `scrubometer.py:87`).
- `ac.getCarTyreCompound(0)` ✓ — current tyre compound short name
  (`scrubometer.py:88`).
- `ac.getTrackName(0)`, `ac.getTrackConfiguration(0)`, `ac.getDriverName(0)`
- `ac.isCarInPit(0)` ✓ — `1` if in the pit *box* (`fuel_tracker.py:150`)
- `ac.isCarInPitline(0)` — `1` if anywhere in the pit *lane*
- `ac.isConnected(0)`, `ac.getCarsCount()`, `ac.getCarLeaderboardPosition(0)`,
  server info (`getServerName`, `getServerIP`, …)
- `ac.sendChatMessage(<str>)` ✓ — posts to in-game chat (`button_box.py:90`)

---

## 4. The other data source: shared memory (`sim_info`)

`ac.getCarState` does **not** expose everything. Fuel, per-section car damage,
session type, time remaining, weather, aids, and a lot of static metadata are
only available through AC's **shared-memory map**. The vendored
`third_party/sim_info.py` reads those memory-mapped structs with `ctypes`.

Apps that need it vendor a copy into their own `third_party/` folder
(`fuel_tracker`, `dmg_report`, `slipometer` each have one). Usage:

```python
from third_party.sim_info import SimInfo

def acUpdate(deltaT):
    siminfo = SimInfo()
    fuel  = float(siminfo.physics.fuel)            # litres
    sess  = siminfo.graphics.session               # AC_SESSION_TYPE int
    track = siminfo.static.track
    siminfo.close()                                # ALWAYS close it
```

There are three structs (see `sim_info.py` for the full field lists):

- **`siminfo.physics`** — live car physics. Highlights:
  `gas`, `brake`, `fuel` ✓, `gear`, `rpms`, `speedKmh`, `tc` ✓, `abs` ✓,
  `drs`, `kersCharge`, `carDamage` (5-float array: front, rear, left, right,
  center — see `dmg_report.py:75`), `wheelSlip[4]`, `tyreWear[4]`,
  `tyreCoreTemperature[4]`, `brakeTemp[4]`, `suspensionTravel[4]`,
  `pitLimiterOn`, `airTemp`, `roadTemp`, `brakeBias`.
- **`siminfo.graphics`** — session/UI state:
  `status` (0 off / 1 replay / 2 live / 3 pause), `session` ✓ (0 practice /
  1 qualify / 2 race / 3 hotlap / 4 time-attack / 5 drift / 6 drag),
  `completedLaps`, `position`, `currentTime`/`lastTime`/`bestTime` ✓ (wide-char
  strings like `"1:23:456"`), `iCurrentTime`/`iBestTime` (ints, ms),
  `sessionTimeLeft` ✓ (ms remaining), `numberOfLaps`, `isInPit`, `isInPitLine`,
  `tyreCompound`, `flag`, `surfaceGrip`, `windSpeed`, `mandatoryPitDone`.
- **`siminfo.static`** — per-session constants:
  `maxFuel`, `maxRpm`, `maxTorque`, `maxPower`, `carModel`, `track`,
  `playerNick`, `numCars`, `aidFuelRate`, `hasDRS`/`hasERS`/`hasKERS`,
  `kersMaxJ`/`ersMaxJ`, `isTimedRace`, `hasExtraLap`, `pitWindowStart/End`.

### Shared-memory rules

- **Always `siminfo.close()`** when done in `acUpdate` (every app does — see
  `fuel_tracker.py:223`, `dmg_report.py:82`). The apps construct a fresh
  `SimInfo()` each `acUpdate` and close it; that's the established pattern here.
- **`ctypes` needs to be importable.** AC's embedded Python doesn't always have
  the C-extension binaries on `sys.path`. Apps that use `sim_info` prepend an
  arch-specific lib dir before importing. `slipometer.py:7` and `dmg_report.py:10`
  do exactly this:

  ```python
  import os, sys, platform
  if platform.architecture()[0] == "64bit":
      libdir = 'third_party/lib64'
  else:
      libdir = 'third_party/lib'
  sys.path.insert(0, os.path.join(os.path.dirname(__file__), libdir))
  os.environ['PATH'] = os.environ['PATH'] + ";."
  from third_party.sim_info import SimInfo
  ```

  > Note: `fuel_tracker.py` imports `SimInfo` *without* that bootstrap and works,
  > so whether you need the lib-dir prepend depends on the player's AC build. If
  > your app imports `sim_info` and crashes on a `_ctypes`/`mmap` import in some
  > installs, add the bootstrap above and vendor the `lib`/`lib64` folders. When
  > in doubt, include it — it's harmless when the binaries are already present.

- The string time fields (`currentTime`, `bestTime`) are formatted like
  `"M:SS:mmm"`. `fuel_tracker.py:256` shows a `lap_time_to_ms` parser for them.

---

## 5. Building the UI

### Window + controls

Create the window in `acMain`, then add controls to it. All "add" calls return
an integer id you store (usually in a module-global) and reuse later.

```python
appWindow = ac.newApp(appName)
ac.setSize(appWindow, width, height)

label = ac.addLabel(appWindow, "initial text")
ac.setPosition(label, x, y)           # x,y relative to the window
ac.setFontSize(label, 40)
ac.setFontAlignment(label, "center")  # "left" | "center" | "right"
ac.setText(label, "new text")         # update later (usually in onFormRender)
```

Controls available (from the PDF):

| Control | Create | Notes |
|---|---|---|
| Label | `ac.addLabel(win, text)` | Text display. By far the most used here. |
| Button | `ac.addButton(win, text)` | Pair with `ac.addOnClickedListener(btnId, fn)`. Callback signature is `fn(v1, v2)` — see `button_box.py:88`. |
| Spinner | `ac.addSpinner(win, label)` | Numeric stepper. `setRange(id, min, max)`, `setValue`, `setStep`, `getValue`, `addOnValueChangeListener`. See `state_of_kachow.py:89`. |
| Check Box | `ac.addCheckBox(win, name)` | `ac.addOnCheckBoxChanged(id, fn)`; callback is `fn(name, value)` where value is 1/-1. See `popUpAirBrake.py:41`. |
| Progress Bar | `ac.addProgressBar(win, text)` | `setValue` / `setRange`. |
| Input Text | `ac.addInputText(win, text)` | `setFocus`, `addOnValidateListener` (fires on Enter). |
| List Box | `ac.addListBox(win, name)` | `addItem`, `removeItem`, selection listeners. |
| Graph | `ac.addGraph(win, name)` | `addSerieToGraph(id, r,g,b)`, `addValueToGraph(id, serie, val)`, `setRange`. (None of the current apps use this — `scrubometer` hand-draws its own graph with quads instead.) |

Other window/control tweaks: `ac.setTitle`, `ac.setBackgroundOpacity(id, 0..1)`,
`ac.drawBackground(id, 0|1)`, `ac.drawBorder(id, 0|1)`,
`ac.setBackgroundColor(id, r,g,b)`, `ac.setFontColor(id, r,g,b,a)`,
`ac.setVisible(id, 0|1)`, `ac.setBackgroundTexture(id, path)`.

### Custom drawing (immediate-mode GL)

For anything beyond text — bars, boxes, meters — draw with the GL helpers
**inside `onFormRender`**. The coordinate origin is the window's top-left; `x`
grows right, `y` grows down. Units are pixels.

```python
ac.glColor3f(1, 0, 0)          # set color (r,g,b in 0..1); persists until changed
ac.glQuad(x, y, w, h)          # filled rectangle — the workhorse
ac.glColor4f(1, 0, 0, 0.5)     # color with alpha
```

`ac.glQuad(x, y, w, h)` is used everywhere. A 1px-thick quad is a line, which is
how every app draws outlines. The repeated `draw_box` helper (copy-pasted into
`slipometer.py:88`, `scrubometer.py:152`, `liftLag.py:82`, `state_of_kachow.py:173`)
is the idiom:

```python
def draw_box(x, y, width, height):
    ac.glColor3f(0, 1, 0)
    ac.glQuad(x, y, width, 1)            # top edge
    ac.glQuad(x, y + height - 1, width, 1)   # bottom edge
    ac.glQuad(x, y, 1, height)          # left edge
    ac.glQuad(x + width - 1, y, 1, height)   # right edge
```

To draw a *filled, value-driven* bar (a meter), draw a quad whose width or height
is a fraction of the full size. `state_of_kachow.py:199` scales a bar by a
percentage; `slipometer.py` fills tyre boxes proportionally to slip. Clamp the
fraction to `[0,1]` and `max(..., 0)` the pixel size so you never pass a negative
width.

There's also `ac.glBegin/glVertex2f/glEnd` for lines/triangles and
`ac.newTexture(path)` + `ac.glQuadTextured(...)` for textured quads, but the
existing apps stick to `glQuad`. Reach for those only if a plain quad won't do.

### Sizing/layout convention

Apps define `window_width`/`window_height` (and sometimes a `size_mult` /
`app_scale_factor`) as module globals, then express every position as a fraction
of those (`slipometer.py:28-36`, `scrubometer.py:68-75`). Doing the same keeps
your layout resolution-independent and easy to rescale. Pick the window size to
fit your content and set it once with `ac.setSize(appWindow, w, h)`.

---

## 6. Patterns you'll reuse (straight from the apps)

### Logging / debugging

Every app defines the same three helpers — copy them verbatim:

```python
def log_to_file(msg):    ac.log(appName + ": " + str(msg))      # → AC log.txt
def log_to_console(msg): ac.console(appName + ": " + str(msg))  # → in-game py console
def log(msg):            ac.log(...); ac.console(...)           # both
```

`ac.log` writes to AC's `log.txt`; `ac.console` writes to the in-game Python
console (open it with the console app / the backtick-style toggle). **This is
your only debugger** — there's no breakpoint, no stdout. Log liberally while
developing. `state_of_kachow.py:140` shows a throttled debug dump (every 100
ticks) gated behind a `debug` flag so you don't spam the log every frame.

### Detecting a new lap

Compare `LapCount` against a stored previous value; when it changes, do your
per-lap rollover, then update the stored value. Both `fuel_tracker.py:163` and
`state_of_kachow.py:118` do this:

```python
current_lap = ac.getCarState(0, acsys.CS.LapCount)
if current_lap != last_lap_count:
    # ... close out the previous lap ...
    last_lap_count = current_lap
```

Note `fuel_tracker` uses `!=` (inequality) deliberately rather than `>` so that a
*session change* that resets the lap counter still triggers the rollover (see the
git history note "Lap change now uses inequality").

### Detecting a session change / reset

Read `siminfo.graphics.session` and compare to a stored value; reset your state
when it differs. `fuel_tracker.py:84` (`check_session_change`) + `reset_all()` is
the template for "start fresh each practice/qualy/race."

### Handling the pit box

`ac.isCarInPit(0)` is true when stationary in the box. `fuel_tracker.py:150`
invalidates the current lap's fuel sample while in the pit so a pit-and-refuel
doesn't corrupt the per-lap average. If your metric is lap-based, decide what a
pit stop should do to it.

### Reading the car's data files (.ini / .lut)

Some physics constants aren't in telemetry at all — they live in the car's data
files on disk. Build the path from `ac.getCarName(0)` and the hardcoded Steam
install path, then parse:

- `scrubometer.py:85` opens `…\content\cars\<car>\data\tyres.ini` and parses the
  `FRICTION_LIMIT_ANGLE` per compound. It wraps the open in `try/except
  FileNotFoundError` and shows a "Data not found" label, because the car's data
  may be packed (in `data.acd`) rather than loose. **Always handle the missing /
  packed-data case** — you cannot rely on the files being unpacked.
- `liftLag.py:162` parses `.lut` lookup tables (`height_front_CL.lut`) which are
  `key|value` per line, into a dict, then linearly interpolates.

This is powerful but brittle: it depends on the user's exact install path and on
data being unpacked. Gate it behind try/except and degrade gracefully.

### Persisting settings between sessions

There's no settings API. Write a small file next to your script.
`popUpAirBrake.py:46` reads/writes `options.dat` via
`os.path.join(os.path.dirname(__file__), 'options.dat')` to remember a checkbox
state across launches. Use `__file__`-relative paths so it works regardless of
where AC is installed.

### Loading a config file

`button_box.py:19` reads a `buttons.config` (pipe-delimited, `#` comments) to make
the app data-driven. Format is dead simple:

```
#button_name|chatmsg
VSC|VSC In Effect!
```

Note that app currently opens the config via a path **relative to the AC working
directory** (`apps/python/button_box/buttons.config`, `button_box.py:22`) rather
than `__file__`-relative. The `__file__`-relative approach used by `popUpAirBrake`
is more robust — prefer it for new apps.

### Sending chat / triggering key presses

- `ac.sendChatMessage(text)` posts to multiplayer chat (`button_box.py`).
- To press a *keyboard* key (e.g. toggle lights), there's no AC API — you call the
  Windows `SendInput` via `ctypes`. `popUpAirBrake` vendors `directkeys.py`
  (`PressKey`/`ReleaseKey` with virtual key codes) and pulses it. This is
  Windows-only and a bit of a hack; only reach for it when AC genuinely has no API
  for what you want.

### Smoothing noisy telemetry

Raw telemetry is jittery. `fuel_tracker.py:198` keeps a list of per-lap samples
and averages only those within one standard deviation to throw out outlier laps
(out-laps, mistakes). `iamspeedKMH.py` tracks rolling min/cur/max with simple
comparisons. Decide how much history you keep and trim it (`scrubometer.py:211`
caps its series to the pixel width and `pop(0)`s the oldest).

---

## 7. Creating a new app

A helper script scaffolds a new app from the template
(`python/template/template.sh`). Run it from the `python/` directory:

```sh
cd python
./template/template.sh my_new_app
```

It copies `template/` to `my_new_app/`, renames `template.py` →
`my_new_app.py`, and `sed`s the internal `template` name to `my_new_app`. Then:

1. Edit `my_new_app/my_new_app.py` — build your UI in `acMain`, read data in
   `acUpdate`, draw in `onFormRender`.
2. If you need fuel/damage/session data, vendor `third_party/sim_info.py` (copy
   from an app that has it, e.g. `fuel_tracker/third_party/sim_info.py`), and add
   the lib-dir bootstrap from §4 if your testers hit a `_ctypes` import error.
3. Write a short `README.md` (every app has one — keep it to a description +
   usage; see any existing app's README).
4. Drop a screenshot/gif under `static/assets/my_new_app/` if you want it in the
   gallery (these are web-only and not shipped in the release zip).

### Naming consistency (important)

Keep these four identical (or consistently derived):
folder name · `<app>.py` filename · `appName` global · the `ac.newApp(appName)`
argument · the string `acMain` returns. The release zip and AC's loader key off
the folder/file names, so mismatches cause apps not to load.

---

## 8. Testing & deploying

There is **no offline test path** — `ac`/`acsys` only exist in-game, and
`sim_info` needs the running game's shared memory. The realistic loop is:

1. Copy your app folder into `…/assettocorsa/apps/python/<app>/`.
2. Enable it under Options → General → UI Modules and restart AC if needed.
3. Drive (or sit in a session) and watch behavior; tail AC's `log.txt` and the
   in-game Python console for your `ac.log`/`ac.console` output and any
   tracebacks.
4. A Python exception during `acMain` usually means the app silently fails to
   appear — check the log first.

Static syntax/lint checks (`python -m py_compile`, a linter) are still worth
running locally to catch typos before copying in, even though you can't execute
the app. Just remember the `ac`/`acsys` imports will be unresolved off-game.

### Release

Pushing to `main` triggers `.github/workflows/release.yml`, which zips `python/`
into `TurnRightToGoLeft-latest.zip` and updates the `latest` GitHub release. So:
everything an app needs at runtime must be **inside its folder** (vendored libs,
config, data files) — nothing outside `python/` ships.

---

## 9. Gotchas & conventions checklist

- [ ] `acMain` returns the app-name string.
- [ ] Render callback registered with `ac.addRenderCallback`.
- [ ] All drawing happens in `onFormRender`, not `acUpdate`.
- [ ] Compute in `acUpdate`, display in `onFormRender`.
- [ ] Control ids and mutable state are module globals; functions `global`-declare
      what they assign (every app does this — it's verbose but required).
- [ ] If using `SimInfo`, construct it and `close()` it each `acUpdate`.
- [ ] `getCarState` returns `0` on failure and per-wheel values are
      `(FL, FR, RL, RR)`; lap/best times are in **milliseconds**;
      `RideHeight` is a `[front, rear]` pair.
- [ ] Reading car data files: wrap in try/except, handle packed (`data.acd`) data,
      expect the hardcoded Steam path
      `C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\`.
- [ ] Persisted/config files use `os.path.dirname(__file__)`-relative paths and
      live inside the app folder so they survive the release zip.
- [ ] Copy the `log_to_file`/`log_to_console`/`log` trio — logging is your only
      debugger.
- [ ] AC's Python is **3.3 with no pip**. No third-party packages — vendor any
      external pure-Python code into the app folder. No f-strings/walrus/etc.;
      the existing apps use `.format()` and `+`-concatenation. Match that style.
- [ ] Windows-only when you touch `ctypes`/`SendInput` (e.g. `directkeys`).

---

## 10. Quick map of the example apps

Use these as references for specific techniques:

| App | Good example of |
|---|---|
| `template` | Bare lifecycle skeleton; the scaffolding script. |
| `iamspeedKMH` / `iamspeedMPH` | Labels + boxes, rolling min/cur/max from `getCarState`. |
| `slipometer` | `sim_info` (tc/abs) + per-wheel `SlipRatio`, proportional filled boxes, lib-dir bootstrap. |
| `scrubometer` | Hand-drawn time-series graph with quads, parsing `tyres.ini`, graceful "data not found". |
| `liftLag` | Parsing `.lut` files + linear interpolation, `RideHeight` 2-tuple. |
| `fuel_tracker` | `sim_info` fuel, per-lap rollover, session-change reset, pit handling, outlier-trimmed averaging, lap-time string parsing. |
| `dmg_report` | `sim_info.physics.carDamage` 5-array, lib-dir bootstrap. |
| `state_of_kachow` | ERS/KERS telemetry, Spinner control with live value, value-driven bar + markers. |
| `button_box` | Buttons + click listeners, data-driven config file, `sendChatMessage`. |
| `popUpAirBrake` | Checkbox control, persisting state to a file, Windows key injection via `directkeys`. |

---

*Authoritative API reference: `ACPythonDocumentation.pdf` in the repo root. This
guide summarizes the parts the repo uses; consult the PDF for the full control
API (list boxes, graphs, camera control, server info, textures, etc.).*
