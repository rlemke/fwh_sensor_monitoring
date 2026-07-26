# Analysis — anomaly detection & alert classification

**Namespace:** `monitor.Analysis` ·
**FFL:** `src/sensor_monitoring/ffl/monitor.ffl` (namespace `monitor.Analysis`) ·
**Handlers:** `src/sensor_monitoring/handlers/analysis/analysis_handlers.py` ·
**Tools:** `src/sensor_monitoring/tools/{detect_anomaly,classify_alert}.py` ·
**Stubs:** `src/sensor_monitoring/tools/_lib/sensor.py` (`detect_anomaly`, `classify_alert`) ·
**Tests:** `tests/test_sensor_handlers.py` (`TestAnalysisHandlers`)

## Overview

Analysis is the decision tier: given a `SensorReading`, decide whether its value
is anomalous relative to a four-band threshold config, and if so turn that into a
routable alert. It answers "is this reading out of bounds, and how urgent is it?"
It sits between [ingestion](ingestion.md) (which produces the reading) and
[reporting](reporting.md) (which rolls the anomaly + alert into a report).

## How it works

Two stubs in `tools/_lib/sensor.py`:

1. **`detect_anomaly(reading, threshold_low, threshold_high, critical_low, critical_high)`**
   compares `reading["value"]` against four bands, in priority order:
   `value <= critical_low` -> `critical` / `"critical_low"`; `value >= critical_high`
   -> `critical` / `"critical_high"`; `value <= threshold_low` -> `warning` / `"low"`;
   `value >= threshold_high` -> `warning` / `"high"`; otherwise `normal` / `"none"`.
   `deviation` is the absolute overshoot past the breached bound (rounded to 4 dp);
   `is_anomaly = severity != "normal"`. The critical bands are checked **first**, so
   a value can only be one severity. Returns an `AnomalyResult` dict.
2. **`classify_alert(anomaly, sensor_id, override_config=None)`** maps
   `anomaly["severity"]` to a priority via `{"critical": 1, "warning": 2,
   "normal": 3}` and a channel. With no override the channel is `"default"`; an
   `override_config` may supply its own `priority_map` and `channel`. Returns an
   `AlertPayload` dict.

The handlers (`handle_detect_anomaly`, `handle_classify_alert`) coerce string
inputs (`float(...)` for each threshold, `json.loads(...)` for `reading` /
`anomaly` / `override_config`), map `"null"` -> `None`, log a `_step_log` line, and
return the FFL-shaped dict.

## Fan-out

**Single-task per reading — no fan-out inside this namespace.** `DetectAnomaly` is,
however, the facet `BatchMonitor` fans out per sensor (nested `andThen` under the
`foreach` — see [workflows](workflows.md)); `ClassifyAlert` runs once per reading in
the single-sensor `MonitorSensors` pipeline.

## Data & fields

- **`AnomalyResult`** (schema `monitor.types.AnomalyResult`): `is_anomaly: Boolean`,
  `severity: String` (`normal` | `warning` | `critical`), `deviation: Double`,
  `threshold_breached: String` (`none` | `low` | `high` | `critical_low` |
  `critical_high`).
- **`AlertPayload`** (schema `monitor.types.AlertPayload`): `sensor_id: String`,
  `anomaly: Json`, `priority: Int` (1 = critical … 3 = normal), `channel: String`.
- **Threshold config** — four `Double`s. In the workflows these come from a
  `ThresholdConfig` schema instance `low=-10.0, high=50.0, critical_low=-40.0,
  critical_high=80.0`; **negative thresholds** (via FFL unary negation) are the
  headline case this example exercises.

Mechanism: a four-branch Python threshold predicate over `reading["value"]` and a
dict priority-map lookup — no OSM tags, no spatial filter.

## External libraries / binaries

**None beyond stdlib.** `detect_anomaly` / `classify_alert` use only builtins
(comparisons, dict `.get()`); handlers add `json` + `os`. No binaries.

## Facets & workflows

| Facet | Kind | Effect / Cost | Purpose (from FFL docstring) |
|---|---|---|---|
| `DetectAnomaly(reading: Json, threshold_low: Double, threshold_high: Double, critical_low: Double, critical_high: Double)` -> `(result: AnomalyResult)` | event | pure / free | "Detect anomalies using threshold values including negative thresholds." |
| `ClassifyAlert(anomaly: Json, sensor_id: String, override_config: Json = null)` -> `(alert: AlertPayload)` | event | pure / free | "Classify alert severity; null override_config uses default priority." |

Both are declared as `prompt`-block event facets in `monitor.ffl` but served by the
registered deterministic handlers in `analysis_handlers.py` (`_DISPATCH` +
`handle`), so they run offline. Both carry `with Effect(kind="pure")` +
`with Cost(tier="free")` — pure functions of their inputs.

## Cache / output

**None.** In-memory dicts / stdout JSON only; the stubs do no I/O.

## Gotchas & notes

- **Critical bands win.** Because `critical_low`/`critical_high` are tested before the
  warning bands, a reading below both `critical_low` and `threshold_low` is reported
  as `critical` with `threshold_breached="critical_low"` (see
  `test_detect_anomaly_negative_threshold`: value -45 vs `critical_low=-40` ->
  `deviation=5.0`, `critical`).
- **CLI default drift.** The `detect-anomaly` CLI's argparse defaults
  (`threshold_low=10, threshold_high=40, critical_low=-10, critical_high=60`) differ
  from the handler defaults and the workflow's `ThresholdConfig`
  (`-10 / 50 / -40 / 80`). Pass explicit thresholds when reproducing a workflow run
  from the CLI.
- **`"null"` override sentinel.** `handle_classify_alert` maps a `"null"` string (and
  JSON `null`) to `None`, so FFL's `override_config = null` selects the default
  priority map (`test_classify_null_override`).

## Related specs

- [ingestion](ingestion.md) — produces the `SensorReading` fed to `DetectAnomaly`.
- [reporting](reporting.md) — `RunDiagnostics` / `GenerateSummary` consume the
  `AnomalyResult` and `AlertPayload`.
- [workflows](workflows.md) — wires detect -> classify in `MonitorSensors` and fans
  `DetectAnomaly` out in `BatchMonitor`.
