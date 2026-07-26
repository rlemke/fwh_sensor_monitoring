# Sensor Monitoring — Feature Specifications

This directory holds one **spec per feature** of the `fwh_sensor_monitoring`
example. Each document follows a common shape ([`SPEC_TEMPLATE.md`](SPEC_TEMPLATE.md))
and states, for that feature: how it works, whether and how it **fans out** across
the fleet, what **data & fields** it reads/writes, the **external libraries/binaries**
it relies on, its **facets & workflows**, and its **cache/output**. Claims are
grounded in the FFL `/** … */` docstrings (`src/sensor_monitoring/ffl/monitor.ffl`),
the handler code, the `tools/_lib` stubs, and the tests — the source of truth for each
facet remains its FFL docstring; these specs are the feature-level narrative over them.

**Start here:** [**Workflows & FFL feature showcase**](workflows.md) — the flagship.
It composes all six event facets into the `MonitorSensors` (single-sensor) and
`BatchMonitor` (per-sensor foreach fan-out) workflows and is the first example to
exercise unary negation, null literals, computed map indexing, and mixin aliases.

## Pipeline stages (one spec per FFL namespace)

| Spec | What it covers |
|------|----------------|
| [ingestion.md](ingestion.md) | `monitor.Ingestion` — `IngestReading` (raw args -> `SensorReading`, initial/continuous quality) + `ValidateReading` (calibration offset/scale + range check). |
| [analysis.md](analysis.md) | `monitor.Analysis` — `DetectAnomaly` (four-band thresholds incl. negatives -> `AnomalyResult`) + `ClassifyAlert` (severity -> priority/channel `AlertPayload`). |
| [reporting.md](reporting.md) | `monitor.Reporting` — `RunDiagnostics` (health status from anomaly history) + `GenerateSummary` (aggregate `MonitoringSummary` + report line). |

## Composition & orchestration

| Spec | What it covers |
|------|----------------|
| [workflows.md](workflows.md) | **Flagship.** `monitor.workflows` (`MonitorSensors`, `BatchMonitor`), the `monitor.types` schemas, `monitor.mixins` (`RetryPolicy`/`AlertConfig` + implicits), fan-out, and the FFL language-feature showcase. |

## Package plumbing & tooling

| Spec | What it covers |
|------|----------------|
| [tools-and-lib.md](tools-and-lib.md) | The tools/handlers/`_lib` pattern: six deterministic-stub CLIs + `.sh` wrappers, the `handlers/shared/sensor_utils.py` shim, and the `./sensor` domain dispatcher. |
| [runner-and-catalog.md](runner-and-catalog.md) | The `facetwork.domains` entry point + `DomainPackage`, RegistryRunner-first agent entry points (`agent_registry.py` / `agent.py`), `_DISPATCH`/registration wiring, and the `catalog.yaml` capability manifest. |

---

*Every facet in this package is a stdlib-only deterministic stub — the whole example
runs fully offline, writes **no cache and no durable output**, and needs no API key.
See also the machine-readable capability index at
[`src/sensor_monitoring/catalog.yaml`](../src/sensor_monitoring/catalog.yaml)
(workflows + facets by intent), the repo [`CLAUDE.md`](../CLAUDE.md) (domain contract)
and [`README.md`](../README.md). The live/queryable interface is the MCP
`fw_capabilities` / `fw_catalog_search` / `fw_describe_handler` tools.*
