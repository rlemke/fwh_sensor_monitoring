# Reporting — diagnostics & monitoring summary

**Namespace:** `monitor.Reporting` ·
**FFL:** `src/sensor_monitoring/ffl/monitor.ffl` (namespace `monitor.Reporting`) ·
**Handlers:** `src/sensor_monitoring/handlers/reporting/reporting_handlers.py` ·
**Tools:** `src/sensor_monitoring/tools/{run_diagnostics,generate_summary}.py` ·
**Stubs:** `src/sensor_monitoring/tools/_lib/sensor.py` (`run_diagnostics`, `generate_summary`) ·
**Tests:** `tests/test_sensor_handlers.py` (`TestReportingHandlers`)

## Overview

Reporting closes the pipeline: it assembles a per-sensor health diagnostic from the
anomaly result, then aggregates the diagnostic + alert into a monitoring summary
with a human-readable report line. It answers "given what we found, is this sensor
healthy, and what's the one-line status?" It consumes the outputs of
[analysis](analysis.md) (and the reading from [ingestion](ingestion.md)) and is the
terminal step of `monitor.workflows.MonitorSensors`.

## How it works

Two stubs in `tools/_lib/sensor.py`:

1. **`run_diagnostics(sensor_id, anomaly_result, reading)`** derives
   `readings_checked = _hash_int("diag:<sensor_id>", 10, 100)` and
   `anomalies_found = _hash_int("diag_anom:<sensor_id>", 0, readings_checked // 4)` —
   both md5-seeded deterministic integers, not real history. If
   `anomaly_result["is_anomaly"]` is true, `anomalies_found` is floored to at least 1.
   `health_status` is `"degraded"` when `anomalies_found > readings_checked * 0.1`,
   else `"healthy"`. Returns a `DiagnosticReport` dict.
2. **`generate_summary(sensor_id, diagnostic, alert)`** rolls up
   `total_anomalies = diagnostic["anomalies_found"]`, `critical_count = 1 if
   alert["priority"] == 1 else 0`, and a formatted `report` string; `total_sensors`
   is hard-coded to 1 (single-sensor summary). Returns a `MonitoringSummary` dict.

The handlers (`handle_run_diagnostics`, `handle_generate_summary`) `json.loads(...)`
any string-encoded `anomaly_result` / `reading` / `diagnostic` / `alert`, append a
`_step_log` line, and return the FFL-shaped dict.

## Fan-out

**Single-task per sensor — no fan-out inside this namespace.** Both facets run once
in the linear tail of `MonitorSensors`; `BatchMonitor` does **not** invoke reporting
(its foreach stops at ingest + detect — see [workflows](workflows.md)).

## Data & fields

- **`DiagnosticReport`** (schema `monitor.types.DiagnosticReport`): `sensor_id: String`,
  `readings_checked: Int`, `anomalies_found: Int`, `health_status: String`
  (`healthy` | `degraded`).
- **`MonitoringSummary`** (schema `monitor.types.MonitoringSummary`): `total_sensors:
  Int`, `total_anomalies: Int`, `critical_count: Int`, `report: String` (the
  `"Sensor <id>: <health>, <n> anomalies, <c> critical"` line).

Mechanism: deterministic hashlib-seeded counts + threshold-ratio health rule +
dict aggregation. No filtering, no external data.

## External libraries / binaries

**None beyond stdlib.** `run_diagnostics` uses `hashlib` (via the `_hash_int`
helper); `generate_summary` uses only builtins + an f-string; handlers add `json` +
`os`. No binaries.

## Facets & workflows

| Facet | Kind | Effect / Cost | Purpose (from FFL docstring) |
|---|---|---|---|
| `RunDiagnostics(sensor_id: String, anomaly_result: Json, reading: Json)` -> `(report: DiagnosticReport)` | event | pure / cheap | "Run diagnostics on a sensor's anomaly history." |
| `GenerateSummary(sensor_id: String, diagnostic: Json, alert: Json)` -> `(summary: MonitoringSummary)` | event | pure / free | "Generate monitoring summary across all processed readings." |

Both are `prompt`-block event facets in `monitor.ffl`, served at runtime by the
deterministic handlers in `reporting_handlers.py`. Both carry
`with Effect(kind="pure")`; `RunDiagnostics` is `with Cost(tier="cheap")`,
`GenerateSummary` is `with Cost(tier="free")`.

## Cache / output

**None.** In-memory dicts / stdout JSON only. The `report` string is returned in the
payload, not written to any file or map.

## Gotchas & notes

- **Deterministic, synthetic history.** `readings_checked` / `anomalies_found` are
  hashed from the sensor id — they are a reproducible stand-in for a real anomaly
  history, not counts of actual readings processed. Swap `run_diagnostics` for a
  real query when wiring a live datastore (keep the return shape).
- **`total_sensors = 1` always.** `generate_summary` is a single-sensor rollup; a true
  fleet-wide aggregate across many sensors is not implemented here (`BatchMonitor`
  emits a batch string, not a `MonitoringSummary`).
- **CLI arg name.** The `run-diagnostics` CLI takes `--anomaly` (dest
  `anomaly_result`) + `--reading`, both required — unlike the README quickstart
  snippet which shows `run-diagnostics.sh --sensor-id temp-001` alone.

## Related specs

- [analysis](analysis.md) — produces the `AnomalyResult` / `AlertPayload` consumed here.
- [ingestion](ingestion.md) — produces the `reading` argument to `RunDiagnostics`.
- [workflows](workflows.md) — `MonitorSensors` ends with `RunDiagnostics` ->
  `GenerateSummary`.
