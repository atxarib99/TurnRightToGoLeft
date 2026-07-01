"""getCarState identifier -> return shape, plus default scalar values.

AC's ``ac.getCarState(carId, ident)`` returns different shapes depending on the
identifier, and apps unpack the result positionally, e.g.::

    fl, fr, rl, rr = ac.getCarState(0, acsys.CS.SlipRatio)
    front, rear   = ... RideHeight ...

If the mock returns the wrong arity the app dies with a ValueError, so the mock
must know the shape of every identifier it serves.

Shapes:
  'scalar' -> a single number
  'v2'     -> 2-tuple  (front, rear)        e.g. RideHeight
  'v3'     -> 3-tuple  (x, y, z)            e.g. AccG, Velocity
  'v4'     -> 4-tuple  (FL, FR, RL, RR)     e.g. SlipRatio, tyre temps

The identifiers used by the apps in this repo are grep-confirmed and exact. The
rest are best-effort from ACPythonDocumentation.pdf and may need reconciling if a
future app relies on one. Unknown identifiers default to 'scalar' returning 0,
matching AC's documented "returns 0 on failure" behaviour.
"""

# --- explicit shape table -------------------------------------------------

# 2-tuple (front, rear)
V2 = {
    "RideHeight",
}

# 3-tuple (x, y, z)
V3 = {
    "AccG",
    "Velocity",
    "LocalVelocity",
    "LocalAngularVelocity",
    "WorldPosition",
    "SpeedTotal",
    "WheelAngularSpeed",
}

# 4-tuple (FL, FR, RL, RR)
V4 = {
    "SlipAngle",
    "SlipRatio",
    "CamberRad",
    "CamberDeg",
    "Mz",
    "Load",
    "TyreRadius",
    "NdSlip",
    "TyreSlip",
    "Dy",
    "CurrentTyresCoreTemp",
    "ThermalState",
    "DynamicPressure",
    "TyreLoadedRadius",
    "SuspensionTravel",
    "TyreDirtyLevel",
}

# Identifiers that are conceptually integers (apps may compare / use as counts).
INT_IDENTS = {
    "LapCount",
    "Gear",
    "IsEngineLimiterOn",
    "LapInvalidated",
    "IsDriftInvalid",
}

# Per-identifier default scalar (used when the data source has no value for it).
# Anything not listed defaults to 0.0.
SCALAR_DEFAULTS = {
    # state_of_kachow divides by this at import time, so it must be non-zero.
    "ERSMaxJ": 4_000_000.0,
}


def shape_of(ident):
    """Return 'scalar' | 'v2' | 'v3' | 'v4' for a getCarState identifier."""
    if ident in V2:
        return "v2"
    if ident in V3:
        return "v3"
    if ident in V4:
        return "v4"
    return "scalar"


def arity_of(ident):
    """Number of components for a vector identifier, else 1."""
    return {"v2": 2, "v3": 3, "v4": 4}.get(shape_of(ident), 1)


# Component suffixes used in the CSV schema and synthetic data, per shape.
COMPONENT_SUFFIXES = {
    "v2": ("_F", "_R"),
    "v3": ("_X", "_Y", "_Z"),
    "v4": ("_FL", "_FR", "_RL", "_RR"),
}


def scalar_default(ident):
    return SCALAR_DEFAULTS.get(ident, 0.0)
