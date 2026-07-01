"""Telemetry source feeding both ``ac.getCarState`` and the fake ``sim_info``.

Two modes:
  * synthetic (default): a fabricated, repeating ~90s lap computed as functions of
    time -- speed profile with corners, anti-correlated gas/brake, slip spikes,
    oscillating ride height, monotonically draining fuel, incrementing LapCount,
    cycling ERS. Lets any app render and animate with zero game data.
  * csv: plays back a recorded session, advancing by wall-clock vs the row 't'.

A single current-sample dict is shared by getCarState and sim_info so the two
stay consistent (e.g. fuel_tracker cross-references both).

CSV schema (header row; all columns optional, missing -> defaults):
  t                      sample time in seconds
  <Identifier>           getCarState scalar, e.g. SpeedKMH, Gas, Brake, LapCount
  <Identifier>_FL/_FR/_RL/_RR   per-wheel 4-tuple, e.g. SlipRatio_FL
  RideHeight_F, RideHeight_R    2-tuple
  AccG_X/_Y/_Z                  3-tuple
  physics.<field>        sim_info physics, e.g. physics.fuel, physics.tc
  physics.carDamage0..4         array element
  physics.tyreWear0..3          array element
  graphics.<field>       e.g. graphics.session, graphics.bestTime (string)
  static.<field>         e.g. static.maxRpm, static.track (string)
  carName, tyreCompound, inPit   misc ac.* general-info values
"""

import csv as _csv
import math

from . import arity

LAP_LENGTH = 90.0          # seconds per synthetic lap
START_FUEL = 60.0          # litres
FUEL_PER_LAP = 2.4         # synthetic burn rate

# sim_info fields that are arrays: dotted base -> length.
SIM_ARRAY_FIELDS = {
    "physics.carDamage": 5,
    "physics.tyreWear": 4,
    "physics.wheelSlip": 4,
    "physics.wheelLoad": 4,
    "physics.wheelsPressure": 4,
    "physics.tyreCoreTemperature": 4,
    "physics.brakeTemp": 4,
    "physics.suspensionTravel": 4,
}

# sim_info fields that are strings (default "" instead of 0.0).
SIM_STRING_FIELDS = {
    "graphics.currentTime",
    "graphics.lastTime",
    "graphics.bestTime",
    "graphics.split",
    "graphics.tyreCompound",
    "static.track",
    "static.trackConfiguration",
    "static.carModel",
    "static.carSkin",
    "static.playerName",
    "static.playerSurname",
    "static.playerNick",
    "static._acVersion",
    "static._smVersion",
}


def _ms_to_laptime(ms):
    """Format milliseconds as AC's 'M:SS:mmm' string."""
    ms = int(ms)
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    millis = ms % 1000
    return "%d:%02d:%03d" % (minutes, seconds, millis)


class DataProvider(object):
    def __init__(self, mode="synthetic", csv_path=None, loop=False, scenario="driving"):
        self.mode = mode
        self.loop = loop
        self.scenario = scenario
        self.values = {}
        self._rows = []
        self._max_t = 0.0
        if mode == "csv":
            self._load_csv(csv_path)
        self.update(0.0)

    # -- public --------------------------------------------------------------

    def update(self, elapsed):
        """Advance the current sample to wall-clock ``elapsed`` seconds."""
        if self.mode == "csv":
            self.values = self._sample_csv(elapsed)
        else:
            self.values = synthetic_sample(elapsed, self.scenario)

    def get(self, key, default=0.0):
        return self.values.get(key, default)

    def car_state(self, ident):
        """Return a getCarState value in the correct shape for ``ident``."""
        shape = arity.shape_of(ident)
        if shape == "scalar":
            return self._scalar(ident)
        suffixes = arity.COMPONENT_SUFFIXES[shape]
        return tuple(self._scalar(ident + sfx, base=ident) for sfx in suffixes)

    def sim_field(self, group, name):
        base = group + "." + name
        if base in SIM_ARRAY_FIELDS:
            n = SIM_ARRAY_FIELDS[base]
            return [self.values.get(base + str(i), 0.0) for i in range(n)]
        if base in self.values:
            return self.values[base]
        return "" if base in SIM_STRING_FIELDS else 0.0

    # -- internals -----------------------------------------------------------

    def _scalar(self, key, base=None):
        v = self.values.get(key)
        if v is None:
            v = arity.scalar_default(base or key)
        if (base or key) in arity.INT_IDENTS:
            try:
                return int(v)
            except (TypeError, ValueError):
                return 0
        return v

    def _load_csv(self, path):
        with open(path, "r", newline="") as fh:
            reader = _csv.DictReader(fh)
            for raw in reader:
                row = {}
                for k, v in raw.items():
                    if k is None or v is None or v == "":
                        continue
                    row[k] = _coerce(v)
                if "t" in row:
                    self._rows.append(row)
        self._rows.sort(key=lambda r: r["t"])
        if self._rows:
            self._max_t = self._rows[-1]["t"]

    def _sample_csv(self, elapsed):
        if not self._rows:
            return {}
        t = elapsed
        if self.loop and self._max_t > 0:
            t = elapsed % self._max_t
        # step: latest row whose t <= current time (clamp to first/last)
        chosen = self._rows[0]
        for row in self._rows:
            if row["t"] <= t:
                chosen = row
            else:
                break
        return dict(chosen)


def _coerce(s):
    """CSV cells: numbers become floats, everything else stays a string."""
    try:
        return float(s)
    except (TypeError, ValueError):
        return s


# --- synthetic lap --------------------------------------------------------

def synthetic_sample(t, scenario="driving"):
    """Compute a plausible telemetry sample at time ``t`` seconds."""
    if scenario == "idle":
        return _idle_sample(t)

    lap_t = t % LAP_LENGTH
    frac = lap_t / LAP_LENGTH
    lap_count = int(t / LAP_LENGTH)

    # Speed profile: two slow corners per lap. 0..1 "throttle position" curve.
    corner = 0.5 + 0.5 * math.cos(2 * math.pi * frac * 2.0)   # dips at corners
    speed_kmh = 60.0 + 180.0 * corner                          # ~60..240
    # gas/brake derived from whether we're accelerating out of / braking into.
    slope = math.sin(2 * math.pi * frac * 2.0)
    gas = max(0.0, min(1.0, 0.5 + 0.6 * slope))
    brake = max(0.0, min(1.0, -0.6 * slope)) if scenario != "trail-brake" else max(0.0, -0.4 * slope)
    rpm = 3000 + int(5000 * corner)

    # Slip: spikes near corner apex (low corner value) and under braking.
    base_slip = (1.0 - corner) * 0.18 + brake * 0.05
    slip_fl = base_slip * 0.9
    slip_fr = base_slip * 1.0
    slip_rl = base_slip * 1.1 + gas * 0.04
    slip_rr = base_slip * 1.15 + gas * 0.04

    # Slip angle (degrees) loosely tracks lateral load through corners.
    sa = (1.0 - corner) * 7.0
    # Ride height oscillates with load (mm-ish range around setup).
    rh_front = 0.060 + 0.010 * slope
    rh_rear = 0.075 + 0.012 * slope

    fuel = max(0.0, START_FUEL - FUEL_PER_LAP * (t / LAP_LENGTH))
    best_ms = 90000
    session_left_ms = max(0.0, 1800000.0 - t * 1000.0)   # 30 min session

    # ERS cycling
    kers_charge = 0.5 + 0.5 * math.sin(2 * math.pi * frac)
    ers_max_j = 4_000_000.0

    return {
        # getCarState scalars
        "SpeedKMH": speed_kmh,
        "SpeedMPH": speed_kmh * 0.621371,
        "SpeedMS": speed_kmh / 3.6,
        "Gas": gas,
        "Brake": brake,
        "Clutch": 0.0,
        "RPM": rpm,
        "Gear": 2 + int(4 * corner),
        "LapCount": lap_count,
        "KersCharge": kers_charge,
        "KersInput": max(0.0, gas - 0.7),
        "ERSRecovery": 1.0,
        "ERSDelivery": 2.0,
        "ERSHeatCharging": 1.0,
        "ERSCurrentKJ": kers_charge * ers_max_j / 1000.0,
        "ERSMaxJ": ers_max_j,
        # per-wheel
        "SlipRatio_FL": slip_fl, "SlipRatio_FR": slip_fr,
        "SlipRatio_RL": slip_rl, "SlipRatio_RR": slip_rr,
        "SlipAngle_FL": sa, "SlipAngle_FR": sa,
        "SlipAngle_RL": sa * 0.8, "SlipAngle_RR": sa * 0.8,
        # 2-tuple
        "RideHeight_F": rh_front, "RideHeight_R": rh_rear,
        # 3-tuple
        "AccG_X": slope * 1.5, "AccG_Y": 0.1, "AccG_Z": brake * 1.2,
        # ac general info
        "carName": "ks_lamborghini_huracan_gt3",
        "tyreCompound": "Soft",
        "inPit": 0,
        # sim_info physics
        "physics.fuel": fuel,
        "physics.rpms": rpm,
        "physics.speedKmh": speed_kmh,
        "physics.gas": gas,
        "physics.brake": brake,
        "physics.tc": 0.2,
        "physics.abs": 0.3,
        "physics.carDamage0": min(100.0, lap_count * 1.5),
        "physics.carDamage1": 0.0,
        "physics.carDamage2": 0.0,
        "physics.carDamage3": 0.0,
        "physics.carDamage4": min(100.0, lap_count * 2.0),
        "physics.tyreWear0": max(0.0, 100.0 - t * 0.05),
        "physics.tyreWear1": max(0.0, 100.0 - t * 0.05),
        "physics.tyreWear2": max(0.0, 100.0 - t * 0.06),
        "physics.tyreWear3": max(0.0, 100.0 - t * 0.06),
        # sim_info graphics
        "graphics.session": 2,           # race
        "graphics.completedLaps": lap_count,
        "graphics.position": 1,
        "graphics.currentTime": _ms_to_laptime(lap_t * 1000.0),
        "graphics.bestTime": _ms_to_laptime(best_ms),
        "graphics.lastTime": _ms_to_laptime(best_ms + 1200),
        "graphics.sessionTimeLeft": session_left_ms,
        "graphics.tyreCompound": "Soft",
        "graphics.isInPit": 0,
        # sim_info static
        "static.track": "spa",
        "static.playerNick": "Tester",
        "static.maxRpm": 8500,
        "static.maxFuel": START_FUEL,
        "static.isTimedRace": 1,
        "static.hasExtraLap": 0,
    }


def _idle_sample(t):
    s = synthetic_sample(0.0, scenario="driving")
    # Freeze the car stationary in the pits.
    s.update({
        "SpeedKMH": 0.0, "SpeedMPH": 0.0, "SpeedMS": 0.0,
        "Gas": 0.0, "Brake": 0.0, "RPM": 1100, "Gear": 0, "LapCount": 0,
        "inPit": 1, "graphics.isInPit": 1, "graphics.session": 0,
        "SlipRatio_FL": 0.0, "SlipRatio_FR": 0.0,
        "SlipRatio_RL": 0.0, "SlipRatio_RR": 0.0,
        "SlipAngle_FL": 0.0, "SlipAngle_FR": 0.0,
        "SlipAngle_RL": 0.0, "SlipAngle_RR": 0.0,
    })
    return s


def dump_csv(path, seconds=180.0, dt=0.1, scenario="driving"):
    """Write a synthetic session to ``path`` so CSV playback is testable."""
    # Collect the union of keys across samples (stable header).
    rows = []
    t = 0.0
    keys = set()
    while t <= seconds:
        s = synthetic_sample(t, scenario)
        s_out = {"t": round(t, 3)}
        s_out.update(s)
        rows.append(s_out)
        keys.update(s_out.keys())
        t += dt
    keys.discard("t")
    header = ["t"] + sorted(keys)
    with open(path, "w", newline="") as fh:
        writer = _csv.DictWriter(fh, fieldnames=header)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return path, len(rows)
