# CLAUDE.md — sensor-monitoring

This repository is a **standalone Facetwork example package**. The Facetwork
platform (workflow compiler + runtime) lives at
`/Users/ralph_lemke/facetwork`; this repo only contains the sensor-
monitoring-specific FFL, handlers, and tools. The two are wired
together via the `facetwork.examples` entry point in `pyproject.toml`.

## Quick orientation

```
fwh_sensor_monitoring/
├── pyproject.toml                       # declares the facetwork.examples entry point
├── src/sensor_monitoring/__init__.py    # exports `example: ExamplePackage`
├── src/sensor_monitoring/handlers/      # 3 subpackages + shared/ shim
├── src/sensor_monitoring/ffl/           # monitor.ffl
├── src/sensor_monitoring/tools/         # CLI utilities + _lib/ (sensor stubs)
├── tests/                               # mocked integration tests
└── agent-spec/                          # cross-cutting design specs
```

## Common operations

```bash
# Register this package with Facetwork's runner
pip install -e .

# From a Facetwork checkout:
scripts/seed-examples --include sensor-monitoring
scripts/start-runner --example sensor-monitoring -- --log-format text

# Run as a standalone agent
PYTHONPATH=src python agent_registry.py    # RegistryRunner (primary entry point)
PYTHONPATH=src python agent.py             # legacy AgentPoller

# CLIs — every event facet has one, all backed by tools/_lib/sensor.py
src/sensor_monitoring/tools/ingest-reading.sh --sensor-id temp-001 --value 22.4 --unit celsius
src/sensor_monitoring/tools/detect-anomaly.sh --reading '{"value":120}' --baseline '{"mean":22.5,"std":1.2}'

# Tests
pytest tests/ src/sensor_monitoring/handlers/ -v
```

## Key concepts

### Tools / handlers / _lib pattern

Every facet has two surfaces — a CLI under
`src/sensor_monitoring/tools/` and an FFL handler under
`src/sensor_monitoring/handlers/<domain>/` — and both call into the
**same** deterministic-stub implementation in
`src/sensor_monitoring/tools/_lib/sensor.py`. The shim at
`src/sensor_monitoring/handlers/shared/sensor_utils.py` re-exports the
`_lib` symbols via the **fully-qualified** package path
(`from sensor_monitoring.tools._lib.sensor import …`) so this package
coexists cleanly with sibling Facetwork example packages on
`sys.modules`.

```
                       ┌─────────────────────────────┐
   CLI tool ───────────┤                             │
                       │   tools/_lib/sensor.py      │ ← single source of truth
   FFL handler ────────┤   (6 deterministic stubs)   │
   (via shared shim)   │                             │
                       └─────────────────────────────┘
```

### Handler / domain map

| Subpackage | FFL namespace | Facets / `_lib` functions |
|------------|--------------|---------------------------|
| `ingestion/` | `monitor.Ingestion` | `IngestReading` → `ingest_reading`, `ValidateReading` → `validate_reading` |
| `analysis/` | `monitor.Analysis` | `DetectAnomaly` → `detect_anomaly`, `ClassifyAlert` → `classify_alert` |
| `reporting/` | `monitor.Reporting` | `RunDiagnostics` → `run_diagnostics`, `GenerateSummary` → `generate_summary` |

### Deterministic stubs

`tools/_lib/sensor.py` uses only `hashlib` from stdlib — no clock,
no `random`, no I/O. Same input → same output every time, which makes
tests trivial. When you wire this to a real sensor library, swap the
stubs for real implementations (keep the function signatures and
return shapes intact) and the FFL handlers + CLIs pick up the change
transparently.

## Adding new facets

1. Add a pure stub function to `tools/_lib/sensor.py` (or a new
   `tools/_lib/<domain>.py` module).
2. Re-export the symbol from
   `src/sensor_monitoring/handlers/shared/sensor_utils.py`.
3. Add a CLI wrapper at `src/sensor_monitoring/tools/<verb>-<noun>.py`
   (and `.sh`).
4. Add the handler to the right `handlers/<domain>/<name>_handlers.py`
   and wire it into `_DISPATCH`.
5. Drop the FFL declaration into `src/sensor_monitoring/ffl/`.
6. Re-run `scripts/seed-examples --include sensor-monitoring`.

## Code review checklist

- Keep `_lib/` free of `facetwork.runtime` so CLIs stay runnable standalone.
- Keep stubs deterministic (hashlib-based); no `random`, no time of day.
- For every error handler: never silently return empty defaults. Fail explicitly or re-raise.
- New mixin aliases / null-literal patterns should land in `monitor.ffl` so the FFL stays the canonical reference for those features.
