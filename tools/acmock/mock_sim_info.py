"""Mock of the vendored ``third_party.sim_info`` module.

The real module memory-maps AC's shared memory (``acpmf_physics`` etc.), which
doesn't exist off-game. This replacement exposes the same public surface --
``SimInfo`` with ``.physics`` / ``.graphics`` / ``.static`` attribute bags and a
no-op ``.close()``, plus a module-level ``info`` instance (the real module
creates one at import) -- but reads values from the shared DataProvider.

It is registered into ``sys.modules`` under both ``third_party.sim_info`` and
``sim_info`` before the target app is imported, so the app's
``from third_party.sim_info import SimInfo`` resolves here and the real file
never loads.
"""

from . import mock_ac


class _Bag(object):
    """A physics/graphics/static struct: attribute access -> DataProvider."""

    def __init__(self, group):
        # Use object.__setattr__ to avoid recursing through __getattr__.
        object.__setattr__(self, "_group", group)

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return mock_ac._rt().data.sim_field(object.__getattribute__(self, "_group"), name)


class SimInfo(object):
    def __init__(self):
        self.physics = _Bag("physics")
        self.graphics = _Bag("graphics")
        self.static = _Bag("static")

    def close(self):
        pass

    def __del__(self):
        pass


# The real module instantiates this at import time; mirror that.
info = SimInfo()
