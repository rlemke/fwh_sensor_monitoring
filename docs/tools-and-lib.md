# Tools, `_lib` stubs & the shared-shim pattern

**FFL:** n/a (this is the code-surface feature) ·
**Stubs:** `src/sensor_monitoring/tools/_lib/sensor.py` ·
**CLIs:** `src/sensor_monitoring/tools/*.py` + `*.sh` ·
**Shim:** `src/sensor_monitoring/handlers/shared/sensor_utils.py` ·
**Domain CLI:** `./sensor` (repo root) · **Tools README:** `src/sensor_monitoring/tools/README.md` ·
**Tests:** `tests/test_sensor_handlers.py` (`TestSensorUtils`)

## Overview

Every event facet has **two runnable surfaces** — a terminal CLI and an FFL handler —
and both call into the **same** deterministic-stub implementation in
`tools/_lib/sensor.py`. This spec documents that contract (the tools/handlers/`_lib`
pattern from the framework's `agent-spec/tools-pattern.agent-spec.yaml`) and the
package-coexistence shim. It's how you run one operation from a shell without a
runner, and how the package stays testable offline.

## How it works

```
   CLI tool (tools/<verb>_<noun>.py) ─┐
                                       ├─> tools/_lib/sensor.py   (single source of truth)
   FFL handler (handlers/<ns>/…) ──────┘   (6 deterministic stubs)
        via handlers/shared/sensor_utils.py
```

- **`tools/_lib/sensor.py`** — six pure functions (`ingest_reading`,
  `validate_reading`, `detect_anomaly`, `classify_alert`, `run_diagnostics`,
  `generate_summary`) plus two md5 helpers (`_hash_int`, `_hash_float`). Imports
  **only `hashlib`** — no `facetwork`, no clock, no `random`, no I/O — so the CLIs
  run standalone and the tests are trivially reproducible.
- **CLIs** — one `argparse` script per function (`ingest_reading.py`,
  `validate_reading.py`, `detect_anomaly.py`, `classify_alert.py`,
  `run_diagnostics.py`, `generate_summary.py`), each with a `.sh` wrapper. Contract:
  a one-line human summary on **stderr**, pretty-printed JSON (the same dict shape the
  FFL handler emits) on **stdout**, exit 0 on success. Each imports
  `from sensor_monitoring.tools._lib.sensor import <fn>`.
- **`handlers/shared/sensor_utils.py`** — re-exports the six `_lib` symbols using the
  **fully-qualified** path `from sensor_monitoring.tools._lib.sensor import …`. The
  handlers import from this shim, never from a bare `_lib`.
- **`./sensor`** (repo root) — a generic `fw`-style domain dispatcher, identical
  across every `fwh_*` repo, that auto-discovers `tools/*.sh` and the FFL workflows
  and dispatches by name (`./sensor <command> ...`, `./sensor help`).

## Fan-out

**N/A — single-process CLIs.** These are terminal tools, not distributed tasks; fleet
fan-out is a workflow concern ([workflows](workflows.md)).

## Data & fields

Each CLI's stdout JSON mirrors the corresponding facet return shape (see the
per-facet specs): `{reading, quality}`, `{valid, calibrated_value}`, the
`AnomalyResult`, `AlertPayload`, `DiagnosticReport`, `MonitoringSummary`. The
`tools/README.md` "CLI map" table binds each `<verb>-<noun>.sh` to its
`monitor.<Ns>.<Facet>` and `_lib` function.

## External libraries / binaries

- **`_lib/sensor.py`** — stdlib `hashlib` only. `requirements.txt` states plainly:
  "No external dependencies for the example itself."
- **CLIs** — stdlib `argparse` + `json` + `sys`.
- **`./sensor`** — bash + `awk`/`sed` (no Python needed to list tools).
No binary dependencies anywhere in this feature.

## Facets & workflows

No FFL declarations of its own — this feature is the code substrate under the six
facets documented in [ingestion](ingestion.md), [analysis](analysis.md), and
[reporting](reporting.md). The `_lib` functions are the deterministic implementations
those facets' handlers dispatch to.

## Cache / output

**None durable.** CLIs print to stdout/stderr; nothing is cached or written. (Note:
the repo ships a generic `agent-spec/cache-layout.agent-spec.yaml` — a framework-wide
canonical cache contract — but this package's stubs perform no I/O and use no cache.)

## Gotchas & notes

- **Keep `_lib/` free of `facetwork.runtime`.** Per the repo `CLAUDE.md` review
  checklist, this is what lets the CLIs stay runnable standalone. Adding a runtime
  import here would break `./sensor <tool>` and the offline tests.
- **Fully-qualified imports are deliberate.** The shim imports
  `sensor_monitoring.tools._lib.sensor` (not a bare `_lib`) so this package coexists
  with sibling example packages (osm-geocoder, noaa-weather, census-us, …) that also
  ship a `tools/_lib/`, without a fight for `_lib` on `sys.modules`.
- **CLI/handler default drift.** The CLIs are convenience wrappers; some argparse
  defaults differ from the handler/workflow defaults (e.g. `detect-anomaly`
  thresholds — see [analysis](analysis.md)). Pass explicit args to match a workflow run.
- **Adding a facet touches five files.** New stub -> re-export in the shim -> CLI
  (`.py` + `.sh`) -> handler `_DISPATCH` -> FFL decl (`CLAUDE.md` "Adding new facets").

## Related specs

- [ingestion](ingestion.md) / [analysis](analysis.md) / [reporting](reporting.md) —
  the facets whose handlers call these `_lib` functions.
- [runner-and-catalog](runner-and-catalog.md) — how the handlers that wrap these stubs
  are registered and served.
