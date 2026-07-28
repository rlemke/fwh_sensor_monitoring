# FFL Examples — `sensor-monitoring`

Every numbered scenario is a **complete, compilable FFL file**. Copy one into
`my.ffl` and run it:

```bash
fw ffl run --primary my.ffl \
  --library ~/fw_handlers/fwh_sensor_monitoring/src/sensor_monitoring/ffl/monitor.ffl \
  --workflow my.monitor.<WorkflowName>
```

A runner serving the `monitor` namespace must be up
(`fw runner start --domain sensor-monitoring`). Every block below is
compile-checked against `src/sensor_monitoring/ffl/monitor.ffl`.

New to the language? Start with the
[FFL grammar](https://github.com/rlemke/facetwork/blob/main/docs/reference/language/grammar.md)
and the [canonical examples](https://github.com/rlemke/facetwork/tree/main/examples/canonical).

---

## The building blocks

This domain is the language showcase: **schemas**, **custom mixins with
`implicit` defaults**, pure vs external facets, and a batch fan-out. Nothing here
touches the network, so it is a good place to experiment.

| Declaration | Role |
|---|---|
| `monitor.types.SensorReading` / `ThresholdConfig` / `AnomalyResult` / `AlertPayload` / `DiagnosticReport` / `MonitoringSummary` | **Schemas** — the typed structures the facets exchange |
| `monitor.mixins.RetryPolicy(max_retries = 3, backoff_ms = 1000)` / `AlertConfig(channel, escalate)` | **Custom mixins**, applied fleet-wide by two `implicit` declarations |
| `monitor.Ingestion.IngestReading(sensor_id, value, unit, last_reading) => (reading, quality)` | External: take a reading |
| `monitor.Ingestion.ValidateReading(reading, sensor_config) => (valid, calibrated_value)` | Pure: validate + calibrate |
| `monitor.Analysis.DetectAnomaly(reading, threshold_low, threshold_high, critical_low, critical_high) => (result)` | Pure: threshold check |
| `monitor.Analysis.ClassifyAlert(anomaly, sensor_id, override_config) => (alert)` | Pure: priority + channel |
| `monitor.Reporting.RunDiagnostics(...)` / `GenerateSummary(...)` | Roll a sensor's findings up |
| `monitor.workflows.MonitorSensors` / `BatchMonitor` | The shipped entry points |

`with Effect(kind = "pure")` on most of these is what lets
`fw_capabilities(effect="pure")` find the cheap, side-effect-free primitives.

---

## 1. Run what ships — no FFL to write

```bash
fw ffl seed --include sensor-monitoring

fw ffl run --primary ~/fw_handlers/fwh_sensor_monitoring/src/sensor_monitoring/ffl/monitor.ffl \
  --workflow monitor.workflows.MonitorSensors \
  --inputs '{"sensor_id": "temp-01", "value": 62.0, "unit": "celsius", "sensor_configs": {}}'
```

Write FFL when you want a different *shape* — your own thresholds, extra
validation, a different batch strategy, or your own error handling.

## 2. The smallest workflow you can write

Every FFL workflow needs a `namespace`, a `use` per namespace it calls into, and a
`yield` back to itself.

```ffl
namespace my.monitor {

    use monitor.Ingestion
    use monitor.Analysis

    /** One reading → one anomaly verdict. */
    workflow CheckOne(sensor_id: String, value: Double, unit: String = "celsius") => (severity: String) andThen {

        reading = monitor.Ingestion.IngestReading(
            sensor_id = $.sensor_id, value = $.value, unit = $.unit)

        anomaly = monitor.Analysis.DetectAnomaly(
            reading = reading.reading,
            threshold_low = -10.0,
            threshold_high = 50.0,
            critical_low = -40.0,
            critical_high = 80.0)

        yield CheckOne(severity = anomaly.result.severity)
    }
}
```

Rules visible above: `=>` sits on the **same line** as the closing `)`; references
are always `step.field` (and schema fields nest: `anomaly.result.severity`);
`$.value` reads the workflow's parameter.

## 3. Thresholds as a schema value

A schema is instantiated like a facet call, and its fields are then read off the
step. This keeps a config in one place instead of repeating four literals. Note the
**unqualified** name: `use monitor.types` brings the schema into scope, and schemas
are instantiated by bare name (a namespace-qualified `monitor.types.ThresholdConfig(…)`
is not a valid call).

```ffl
namespace my.monitor {

    use monitor.types
    use monitor.Ingestion
    use monitor.Analysis

    /** One ThresholdConfig, reused by the anomaly check. */
    workflow CheckWithConfig(sensor_id: String, value: Double) => (severity: String, breached: String) andThen {

        cfg = ThresholdConfig(
            low = -10.0, high = 50.0, critical_low = -40.0, critical_high = 80.0)

        reading = monitor.Ingestion.IngestReading(
            sensor_id = $.sensor_id, value = $.value, unit = "celsius")

        anomaly = monitor.Analysis.DetectAnomaly(
            reading = reading.reading,
            threshold_low = cfg.low,
            threshold_high = cfg.high,
            critical_low = cfg.critical_low,
            critical_high = cfg.critical_high)

        yield CheckWithConfig(
            severity = anomaly.result.severity,
            breached = anomaly.result.threshold_breached)
    }
}
```

## 4. The full per-sensor chain

Ingest → detect → classify → diagnose → summarise. Each step references the
previous one, so the runtime runs them in exactly that order.

```ffl
namespace my.monitor {

    use monitor.Ingestion
    use monitor.Analysis
    use monitor.Reporting

    /** One sensor, end to end. */
    workflow FullCheck(sensor_id: String, value: Double, unit: String = "celsius") => (report: String) andThen {

        reading = monitor.Ingestion.IngestReading(
            sensor_id = $.sensor_id, value = $.value, unit = $.unit)

        anomaly = monitor.Analysis.DetectAnomaly(
            reading = reading.reading,
            threshold_low = -10.0, threshold_high = 50.0,
            critical_low = -40.0, critical_high = 80.0)

        alert = monitor.Analysis.ClassifyAlert(
            anomaly = anomaly.result, sensor_id = $.sensor_id)

        diag = monitor.Reporting.RunDiagnostics(
            sensor_id = $.sensor_id,
            anomaly_result = anomaly.result,
            reading = reading.reading)

        summary = monitor.Reporting.GenerateSummary(
            sensor_id = $.sensor_id, diagnostic = diag.report, alert = alert.alert)

        yield FullCheck(report = summary.summary.report)
    }
}
```

## 5. Fan out over many sensors — `foreach`

`andThen foreach v in <list>` runs the body once per element, each as its own set
of runtime steps that the fleet claims in parallel. Here the `foreach` hangs off
the **workflow**, so the loop variable and the workflow's parameters share one `$`.

```ffl
namespace my.monitor {

    use monitor.Ingestion
    use monitor.Analysis

    /** One check per sensor id, in parallel. */
    workflow CheckMany(sensor_ids: Json, value: Double = 25.0, unit: String = "celsius") => (checked: Long) andThen foreach sid in $.sensor_ids {

        reading = monitor.Ingestion.IngestReading(
            sensor_id = $.sid, value = $.value, unit = $.unit)

        anomaly = monitor.Analysis.DetectAnomaly(
            reading = reading.reading,
            threshold_low = -10.0, threshold_high = 50.0,
            critical_low = -40.0, critical_high = 80.0)

        yield CheckMany(checked = 1)
    }
}
```

```bash
fw ffl run --primary my.ffl --library …/monitor.ffl --workflow my.monitor.CheckMany \
  --inputs '{"sensor_ids": ["temp-01", "temp-02", "temp-03"], "value": 62.0}'
```

## 6. Branch on severity — `when`

A `when` block hangs off the step it inspects: inside a case `$` is that step and
`$$` reaches the workflow. Every `when` needs a default case, last, and conditions
must be real `Boolean`s (no truthy coercion).

```ffl
namespace my.monitor {

    use monitor.Ingestion
    use monitor.Analysis

    /** Only classify an alert when the reading actually is anomalous. */
    workflow AlertOnAnomaly(sensor_id: String, value: Double) => (priority: Int) andThen {

        reading = monitor.Ingestion.IngestReading(
            sensor_id = $.sensor_id, value = $.value, unit = "celsius")

        anomaly = monitor.Analysis.DetectAnomaly(
            reading = reading.reading,
            threshold_low = -10.0, threshold_high = 50.0,
            critical_low = -40.0, critical_high = 80.0) andThen when {
            case $.result.is_anomaly == true => {
                alert = monitor.Analysis.ClassifyAlert(
                    anomaly = $.result, sensor_id = $$.sensor_id)
                yield AlertOnAnomaly(priority = alert.alert.priority)
            }
            case _ => {
                yield AlertOnAnomaly(priority = 0)
            }
        }
    }
}
```

## 7. Custom mixins at the call site

`monitor.mixins` declares `RetryPolicy` and `AlertConfig`, and two `implicit`
declarations apply defaults fleet-wide. A call site can override either for one
particular use — and `as <name>` gives the mixin instance a local alias.

```ffl
namespace my.monitor {

    use monitor.Ingestion
    use monitor.mixins

    /** A flaky sensor bus: retry harder, escalate its alerts. */
    workflow StubbornRead(sensor_id: String, value: Double) => (quality: String) andThen {

        reading = monitor.Ingestion.IngestReading(
            sensor_id = $.sensor_id, value = $.value, unit = "celsius") with RetryPolicy(max_retries = 8, backoff_ms = 5000) as retry with AlertConfig(channel = "pager", escalate = true)

        yield StubbornRead(quality = reading.quality)
    }
}
```

## 8. Survive a sensor failure — `catch`

`catch` fires when its step errors after retries are exhausted. Inside a `foreach`
it is per-iteration, so one dead sensor doesn't sink the batch.

```ffl
namespace my.monitor {

    use monitor.Ingestion

    /** Best-effort batch read. */
    workflow BestEffortBatch(sensor_ids: Json, value: Double = 25.0) => (checked: Long) andThen foreach sid in $.sensor_ids {

        reading = monitor.Ingestion.IngestReading(
            sensor_id = $.sid, value = $.value, unit = "celsius") catch {
            yield BestEffortBatch(checked = 0)
        }

        yield BestEffortBatch(checked = 1)
    }
}
```

## 9. Reuse the shipped workflows

```ffl
namespace my.monitor {

    use monitor.workflows

    /** Wrap the shipped batch workflow. */
    workflow BatchWithHeadline(sensor_ids: Json) => (headline: String) andThen {

        run = monitor.workflows.BatchMonitor(sensor_ids = $.sensor_ids, default_value = 25.0)

        yield BatchWithHeadline(headline = "batch: " ++ run.summary)
    }
}
```

---

## Cheat sheet

| You want to… | Write |
|---|---|
| Read a workflow/step parameter | `$.name` (`$$.name` one level out) |
| Read a previous step's result | `stepname.field` (schema fields nest: `anomaly.result.severity`) |
| Instantiate a schema | `use monitor.types` then `cfg = ThresholdConfig(low = …, high = …)` (bare name) |
| Fan out over a list | `workflow W(items: Json) … andThen foreach i in $.items { … }` |
| Override a mixin for one call | `… with RetryPolicy(max_retries = 8) as retry` |
| Handle a step failure | `step = Facet(…) catch { yield … }` |
| Branch | `step = Facet(…) andThen when { case <bool> => { … } case _ => { … } }` |
| Compare | `==`, `!=`, `<`, `>=`, … — always Boolean, never truthy |
| Concatenate strings | `a ++ b` |

**Validate before you run:** `afl my.ffl --check` or MCP `fw_validate`. Every error
carries a `rule_id` — fetch `fw://docs/rules/{rule_id}` for a wrong/right pair.

## See also

- [`docs/README.md`](README.md) — per-feature specs for this domain
- [FFL grammar](https://github.com/rlemke/facetwork/blob/main/docs/reference/language/grammar.md) ·
  [canonical examples](https://github.com/rlemke/facetwork/tree/main/examples/canonical) ·
  [relative `$`-scoping](https://github.com/rlemke/facetwork/blob/main/docs/architecture/ffl-relative-scoping.md)
- `src/sensor_monitoring/ffl/monitor.ffl` — the source of truth for every signature above
