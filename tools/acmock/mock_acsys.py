"""Mock of AC's ``acsys`` module.

In the game, ``acsys`` exposes enum namespaces (``acsys.CS``, ``acsys.CM``, ...)
whose members are opaque constants passed straight back into ``ac.getCarState``
and friends. We don't need the real values: the mock ``ac`` only needs a stable
key to look telemetry up by. So every member resolves to the *string of its own
name* — ``acsys.CS.SpeedKMH == "SpeedKMH"`` — which auto-covers every identifier,
current and future, with zero maintenance.
"""


class _NameSpace(object):
    """Attribute access returns the attribute name as a string.

    ``CS.SpeedKMH`` -> ``"SpeedKMH"``. Caches so identity is stable across calls.
    """

    def __init__(self, label):
        self._label = label
        self._cache = {}

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        val = self._cache.get(name)
        if val is None:
            val = name
            self._cache[name] = val
        return val

    def __repr__(self):
        return "<acsys.%s>" % self._label


# The namespaces AC exposes. CS (car state) is the one the apps use; the others
# are provided so any ``acsys.X`` reference resolves rather than AttributeError-ing.
CS = _NameSpace("CS")   # car state identifiers
CM = _NameSpace("CM")   # camera modes


def __getattr__(name):
    """Any other acsys.<Namespace> resolves to a fresh name-returning namespace."""
    if name.startswith("__"):
        raise AttributeError(name)
    return _NameSpace(name)
