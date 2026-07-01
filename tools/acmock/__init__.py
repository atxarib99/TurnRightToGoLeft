"""acmock: an offline preview + telemetry-playback harness for Assetto Corsa apps.

This package mocks the AC-injected ``ac`` / ``acsys`` modules and the vendored
``third_party.sim_info`` shared-memory reader so an unmodified AC app can be run
on a normal desktop Python, with its UI rendered in the browser and driven by
synthetic telemetry or CSV playback.

Stdlib only. Runs on the developer's modern Python (3.8+); it does NOT change the
fact that the apps themselves must stay Python-3.3 compatible for the game.

Entry point: ``python -m tools.acmock.run <path/to/app.py>``  (see run.py).
"""
