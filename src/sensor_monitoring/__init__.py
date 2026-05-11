"""Sensor monitoring example package — Facetwork workflows + handlers
for ingesting, validating, analyzing, and reporting on time-series
sensor readings.

The example showcases:

- Unary negation (`-10.0`, `-40.0`), null literals as call arguments,
  computed map indexing (`$.configs[step.field]`), and mixin aliases
  (`with RetryPolicy() as retry`)
- RegistryRunner as the primary agent entry point
- Six deterministic-stub event-facet handlers backed by a shared
  ``tools/_lib/sensor`` library that's CLI-runnable standalone

Discovered by the Facetwork runner via the ``facetwork.examples`` entry
point declared in ``pyproject.toml``::

    [project.entry-points."facetwork.examples"]
    sensor-monitoring = "sensor_monitoring:example"

Once ``pip install -e .`` has been run from this repository, Facetwork's
``scripts/start-runner --example sensor-monitoring`` and
``scripts/seed-examples`` will pick this package up automatically.
"""

from __future__ import annotations

from pathlib import Path

from facetwork.examples import ExamplePackage

from .handlers import register_all_registry_handlers

example = ExamplePackage(
    name="sensor-monitoring",
    ffl_dir=Path(__file__).parent / "ffl",
    register_handlers=register_all_registry_handlers,
)
