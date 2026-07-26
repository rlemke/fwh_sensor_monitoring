# Workflows & FFL feature showcase (flagship)

**Namespaces:** `monitor.workflows`, `monitor.types`, `monitor.mixins` ·
**FFL:** `src/sensor_monitoring/ffl/monitor.ffl` ·
**Handlers:** none of their own — compose the ingestion/analysis/reporting facets ·
**Tests:** `tests/test_ffl_compiles.py`, `tests/test_sensor_handlers.py`
(`TestCompilation`, `TestAgentIntegration`)

## Overview

This is the reason the package exists: two end-to-end workflows that compose the six
event facets, and a deliberate showcase of FFL language features that this example
was the **first** to exercise (per the repo `README.md` and `__init__.py`):

- **Unary negation** in expressions — `critical_low = -40.0`, `low = -10.0`.
- **`null` literals as call arguments** — `last_reading = null`, `override_config = null`.
- **Computed map indexing** — `$.sensor_configs[ingest.reading.sensor_id]`.
- **Mixin aliases** — `with RetryPolicy(...) as retry`, `with AlertConfig(...) as alertcfg`.
- **Schema instantiation as a step** — `cfg = ThresholdConfig(...)` inside `andThen`.
- **RegistryRunner as the primary entry point** (see [runner-and-catalog](runner-and-catalog.md)).

`MonitorSensors` is the flagship: a single-sensor pipeline ingest -> validate ->
detect -> classify -> diagnose -> summarize. `BatchMonitor` is the fan-out variant.

## How it works

**`MonitorSensors(sensor_id, value, unit, sensor_configs)`** is a three-phase
workflow (`script` -> `andThen` -> `andThen script`):

1. An opening `script { ... }` block seeds `result["status"]` from `params`.
2. The main `andThen` block: instantiate `cfg = ThresholdConfig(low=-10.0,
   high=50.0, critical_low=-40.0, critical_high=80.0)` as a step, then
   `ingest = IngestReading(...) with RetryPolicy(max_retries=5, backoff_ms=2000) as
   retry`; `validate = ValidateReading(reading = ingest.reading, sensor_config =
   $.sensor_configs[ingest.reading.sensor_id])` (computed map index);
   `detect = DetectAnomaly(reading = ingest.reading, threshold_low = cfg.low, ...)`;
   `classify = ClassifyAlert(... override_config = null) with AlertConfig(...) as
   alertcfg`; `diag = RunDiagnostics(...)`; `summ = GenerateSummary(...)`; then
   `yield MonitorSensors(summary = summ.summary, report = "Sensor " ++ $.sensor_id
   ++ " status: " ++ diag.report.health_status)`.
3. A closing `andThen script` block composes the final `result["report"]`.

Data shape at each hop: raw params -> `SensorReading` (ingest) -> calibrated value
(validate) -> `AnomalyResult` (detect) -> `AlertPayload` (classify) ->
`DiagnosticReport` (diag) -> `MonitoringSummary` (summ). References use `step.field`
form (`ingest.reading`, `detect.result`, `diag.report.health_status`) and `$.attr`
for the workflow's own params.

**`BatchMonitor(sensor_ids, default_value=25.0, unit="celsius")`** instantiates a
shared `batch_cfg = ThresholdConfig(...)` then `andThen foreach sid in $.sensor_ids
{ ... }`: per sensor it runs `reading = IngestReading(sensor_id = $.sid, ...) with
RetryPolicy(max_retries=3) as retry` and a nested `andThen { anomaly =
DetectAnomaly(reading = reading.reading, ...) }`, then `yield BatchMonitor(summary =
"Processed sensor: " ++ $.sid)`. `$.sid` is the loop variable bound on the block's
`$` surface.

## Fan-out

- **`MonitorSensors` — single-task.** One reading, a linear six-facet chain; no
  `foreach`. Wall-clock is the sum of the steps.
- **`BatchMonitor` — per-sensor fan-out.** `foreach sid in $.sensor_ids` emits one
  distributed task per sensor id, each running ingest + detect in parallel across the
  fleet. This is the classic Facetwork fan-out unit (per-leaf = per-sensor); it cuts
  wall-clock from N-sequential to roughly one sensor's latency when runners are
  available. Note the batch loop stops at detect — it does not run classify /
  diagnostics / summary per sensor.

## Data & fields

Six schemas in **`monitor.types`**: `SensorReading`, `ThresholdConfig`,
`AnomalyResult`, `AlertPayload`, `DiagnosticReport`, `MonitoringSummary` (field-level
detail in [ingestion](ingestion.md) / [analysis](analysis.md) /
[reporting](reporting.md)). **`ThresholdConfig{low, high, critical_low,
critical_high}`** is the config both workflows instantiate with negative bounds.

**`monitor.mixins`** declares two mixin facets + two implicits:
`RetryPolicy(max_retries: Int = 3, backoff_ms: Int = 1000)`,
`AlertConfig(channel: String = "default", escalate: Boolean = false)`, plus
`implicit defaultRetry = RetryPolicy(...)` and `implicit defaultAlert =
AlertConfig(...)`. The workflows attach these with `as`-aliases so the mixin's args
arrive under the alias key in the handler payload (verified by
`test_agent_poller_with_mixin_args`: `received_params["retry"]["max_retries"] == 7`).

## External libraries / binaries

**None** — the workflows are pure FFL composition. The facets they call are
stdlib-only Python stubs. Compilation/validation in tests uses `facetwork.parser`
+ `facetwork.validator` (the platform, a pip dep).

## Facets & workflows

| Workflow | Params | Returns | Purpose (FFL docstring) |
|---|---|---|---|
| `MonitorSensors` | `sensor_id: String, value: Double, unit: String, sensor_configs: Json` | `summary: MonitoringSummary, report: String` | "Monitor a single sensor reading end-to-end." |
| `BatchMonitor` | `sensor_ids: Json, default_value: Double = 25.0, unit: String = "celsius"` | `report: String, summary: String` | "Batch monitor multiple sensors using foreach." |

| Mixin facet | Signature | Kind |
|---|---|---|
| `RetryPolicy` | `RetryPolicy(max_retries: Int = 3, backoff_ms: Int = 1000)` | pure mixin (no `event`) |
| `AlertConfig` | `AlertConfig(channel: String = "default", escalate: Boolean = false)` | pure mixin (no `event`) |

Both workflows are entry points (marked `entry_point: true` in
[`catalog.yaml`](../src/sensor_monitoring/catalog.yaml)). The mixins carry no
`Effect`/`Cost` mixins themselves.

## Cache / output

**None.** Workflows return their `MonitoringSummary` / report strings in the run
result; nothing is written to disk, MinIO, or a published site.

## Gotchas & notes

- **Cross-block scoping in `BatchMonitor`.** `anomaly` is scoped inside the nested
  `andThen` under the `foreach`; the loop variable is `$.sid`, and `reading.reading`
  is referenced from the loop-body step. `tests/test_ffl_compiles.py` exists
  specifically because a workflow once referenced a step scoped inside a nested
  `andThen` and validated with an "undefined step" error while still parsing — that
  file validates every shipped `.ffl` clean (parse **and** validate), not just parse.
- **`++` vs `+`.** The workflows use `++` for string concatenation in FFL step
  expressions (`"Sensor " ++ $.sensor_id ++ ...`), while the `script` blocks use
  Python `+` on `params.get(...)`. Don't mix them.
- **Batch summary arithmetic.** `BatchMonitor`'s final yield builds a string with
  `(batch_cfg.high + batch_cfg.critical_high) * 1` — a deliberate demo of numeric
  expression + coercion inside a concat.
- **Compilation invariants under test.** `TestCompilation` asserts 6 schemas, 6 event
  facets, 2 workflows, 2 mixin facets, 2 implicits, >=2 null-literal defaults, the
  `retry` mixin alias, and >=2 unary-negation args — change the FFL and update these.

## Related specs

- [ingestion](ingestion.md), [analysis](analysis.md), [reporting](reporting.md) — the
  facets these workflows compose.
- [runner-and-catalog](runner-and-catalog.md) — how the workflows are seeded, served
  (RegistryRunner), and discovered (catalog manifest).
- [tools-and-lib](tools-and-lib.md) — the CLI mirror of each composed facet.
