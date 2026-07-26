# Ingestion — raw reading intake & validation

**Namespace:** `monitor.Ingestion` ·
**FFL:** `src/sensor_monitoring/ffl/monitor.ffl` (namespace `monitor.Ingestion`) ·
**Handlers:** `src/sensor_monitoring/handlers/ingestion/ingestion_handlers.py` ·
**Tools:** `src/sensor_monitoring/tools/{ingest_reading,validate_reading}.py` ·
**Stubs:** `src/sensor_monitoring/tools/_lib/sensor.py` (`ingest_reading`, `validate_reading`) ·
**Tests:** `tests/test_sensor_handlers.py` (`TestSensorUtils`, `TestIngestionHandlers`)

## Overview

Ingestion is the front of the pipeline: it turns loose call arguments
(`sensor_id`, `value`, `unit`, an optional previous reading) into a structured
`SensorReading`, then optionally validates/calibrates that reading against a
per-sensor config. It answers "take this raw measurement and give me a clean,
range-checked value I can analyze." Everything downstream
([analysis](analysis.md), [reporting](reporting.md)) consumes the
`SensorReading` dict this feature produces.

## How it works

Two independent steps, each backed by one deterministic stub in
`tools/_lib/sensor.py`:

1. **`ingest_reading(sensor_id, value, unit, last_reading=None)`** builds the
   reading dict `{sensor_id, timestamp, value, unit}`. The `timestamp` is **not**
   a clock read — it is `_hash_int("ts:<sensor_id>", 1700000000, 1800000000)`, an
   md5-seeded deterministic integer, so the same sensor id always yields the same
   timestamp (this is what makes the tests reproducible). `quality` is `"initial"`
   when `last_reading is None`, else `"continuous"`. Returns `(reading, quality)`.
2. **`validate_reading(reading, sensor_config=None)`** applies calibration:
   `calibrated = value * calibration_scale + calibration_offset` and checks it is
   within `[min, max]`. With no config it falls back to `calibrated = value` and
   the bound check `-100 <= value <= 100`. Returns `(valid, round(calibrated, 4))`.

The FFL handlers (`handle_ingest_reading`, `handle_validate_reading`) wrap these:
they coerce string inputs to the right types (`float(value)`,
`json.loads(...)` for `reading` / `sensor_config` / `last_reading`), treat the
literal string `"null"` as `None`, append a `_step_log` line, and return the dict
shape the FFL return clause expects. Both the CLI and the handler call the **same**
stub via the `handlers/shared/sensor_utils.py` shim — see [tools-and-lib](tools-and-lib.md).

## Fan-out

**Single-task per reading — no fan-out inside this namespace.** Each facet processes
one reading. Fleet parallelism over many sensors is a workflow concern
(`monitor.workflows.BatchMonitor` fans `IngestReading` out per sensor id via
`foreach`) — see [workflows](workflows.md).

## Data & fields

- **`SensorReading`** (schema `monitor.types.SensorReading`): `sensor_id: String`,
  `timestamp: Long`, `value: Double`, `unit: String`.
- **`quality`** (String, `IngestReading` return): `"initial"` | `"continuous"`.
- **Validation config** (a free-form `Json` map, not a schema): keys
  `calibration_offset` (default 0.0), `calibration_scale` (default 1.0),
  `min` (default −999), `max` (default 999).
- **`ValidateReading` returns** `valid: Boolean`, `calibrated_value: Double`.

Mechanism: plain Python arithmetic + dict `.get()` over the reading/config maps —
no tag filtering, no geospatial selection.

## External libraries / binaries

**None beyond stdlib** for the logic: `tools/_lib/sensor.py` imports only `hashlib`;
the handlers add `json` + `os` (stdlib). No binary dependencies. Package-level pip
deps (`facetwork`, `PyYAML`) are not used by this feature's compute path.

## Facets & workflows

| Facet | Kind | Effect / Cost | Purpose (from FFL docstring) |
|---|---|---|---|
| `IngestReading(sensor_id: String, value: Double, unit: String, last_reading: Json = null)` → `(reading: SensorReading, quality: String)` | event | external / cheap | "Ingest a raw sensor reading with optional last known value." |
| `ValidateReading(reading: Json, sensor_config: Json)` → `(valid: Boolean, calibrated_value: Double)` | event | pure / free | "Validate a reading against sensor-specific configuration." |

Both are declared in FFL as **`prompt`-block** event facets (a `system` /
`template` / `model "claude-sonnet-4-20250514"` block). At runtime this package
registers **deterministic Python handlers** for the same facet names (see
`register_handlers` / `_DISPATCH` in `ingestion_handlers.py`), so execution is
fully offline — the prompt block is the FFL declaration surface, the registered
handler is what actually serves the task. `IngestReading` carries
`with Effect(kind="external")` (a real ingest touches the outside world);
`ValidateReading` is `with Effect(kind="pure")`.

## Cache / output

**None.** Handlers return dicts in memory; the CLIs print JSON to stdout. No cache
namespace, no files, no MinIO/S3 — the stubs do zero I/O.

## Gotchas & notes

- **Deterministic timestamp, not wall-clock.** `ingest_reading` hashes the sensor
  id for `timestamp`; do not read it as a real event time. Swapping in a real
  sensor library is the intended path (keep the return shape) — see the repo
  `CLAUDE.md` "Deterministic stubs".
- **`"null"` sentinel.** `handle_ingest_reading` maps both a JSON-decoded `null` and
  the literal string `"null"` to Python `None` so FFL's `last_reading = null`
  round-trips through string transport. Same trick in `ClassifyAlert` (analysis).
- **Config truthiness.** `validate_reading` treats an empty/`None` config as "no
  config" and uses the ±100 default band — an empty `{}` config also falls through
  to the default band because `if sensor_config:` is falsy for `{}`.

## Related specs

- [analysis](analysis.md) — consumes the `SensorReading` this feature produces.
- [workflows](workflows.md) — orchestrates `IngestReading` in `MonitorSensors`
  (single) and `BatchMonitor` (foreach fan-out).
- [tools-and-lib](tools-and-lib.md) — the CLI + `_lib` + shim contract both facets share.
