"""Handler-side compatibility shim for the sensor-monitoring stubs.

The real implementation lives in
:mod:`sensor_monitoring.tools._lib.sensor`. It is shared verbatim by:

- the ``ingest-reading`` / ``validate-reading`` / ``detect-anomaly`` /
  ``classify-alert`` / ``run-diagnostics`` / ``generate-summary`` CLI
  tools under ``src/sensor_monitoring/tools/``, and
- the FFL ingestion / analysis / reporting handlers (this package's
  siblings).

Imports use the fully-qualified ``sensor_monitoring.tools._lib.sensor``
path so this package coexists cleanly with sibling Facetwork example
packages (osm-geocoder, noaa-weather, jenkins, osm-lz, census-us,
genomics) that also ship a ``tools/_lib/`` directory — there is no
fight for the bare ``_lib`` name on ``sys.modules``.
"""

from __future__ import annotations

from sensor_monitoring.tools._lib import sensor  # noqa: F401
from sensor_monitoring.tools._lib.sensor import (  # noqa: F401
    classify_alert,
    detect_anomaly,
    generate_summary,
    ingest_reading,
    run_diagnostics,
    validate_reading,
)

__all__ = [
    "sensor",
    "classify_alert",
    "detect_anomaly",
    "generate_summary",
    "ingest_reading",
    "run_diagnostics",
    "validate_reading",
]
