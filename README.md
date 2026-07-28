# sensor-monitoring

A standalone [Facetwork](https://github.com/rlemke/facetwork) example package
that ingests, validates, analyzes, and reports on time-series sensor
readings using six event facets backed by a small deterministic-stub
library.

## FFL at a glance

The domain is driven from [FFL](https://github.com/rlemke/facetwork/blob/main/docs/reference/language/grammar.md),
Facetwork's workflow language. A step is `name = Facet(args)`, and each step that
references the previous one is ordered behind it:

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
            threshold_low = -10.0, threshold_high = 50.0,
            critical_low = -40.0, critical_high = 80.0)

        yield CheckOne(severity = anomaly.result.severity)
    }
}
```

```bash
fw ffl run --primary my.ffl --library src/sensor_monitoring/ffl/monitor.ffl \
  --workflow my.monitor.CheckOne \
  --inputs '{"sensor_id": "temp-01", "value": 62.0}'
```

📖 **[docs/ffl-examples.md](docs/ffl-examples.md)** — the full example gallery:
schema instantiation, the full ingest→detect→classify→diagnose chain, `foreach`
fan-out over sensors, `when` branching on severity, this domain's custom mixins
(`RetryPolicy`/`AlertConfig`, incl. `as` aliases) at a call site, and `catch`.
Every snippet there is compile-checked — this domain is a good language showcase
because nothing in it touches the network.

## Feature specifications

Every feature has a spec in [**`docs/`**](docs/README.md) — how it works,
whether/how it **fans out**, its **data & fields**, the **external
libraries/binaries** it uses, its **facets & workflows**, and its **cache/output**
(there is none — the example runs fully offline). Start with the flagship
[**Workflows & FFL feature showcase**](docs/workflows.md); the full index is in
[`docs/README.md`](docs/README.md).

| Area | Specs |
|------|-------|
| **Flagship & composition** | [workflows](docs/workflows.md) |
| **Pipeline stages** | [ingestion](docs/ingestion.md) · [analysis](docs/analysis.md) · [reporting](docs/reporting.md) |
| **Package plumbing** | [tools-and-lib](docs/tools-and-lib.md) · [runner-and-catalog](docs/runner-and-catalog.md) |

The example is also the first showcase of:

- Unary negation in FFL expressions (`-10.0`, `-40.0`)
- `null` literals as call arguments (`last_reading = null`)
- Computed map indexing (`$.configs[step.field]`)
- Mixin aliases (`with RetryPolicy() as retry`)
- RegistryRunner as the primary agent entry point (no `agent.py` polling loop required)

Six event facets across three FFL namespaces:

| Namespace | Facets |
|-----------|--------|
| `monitor.Ingestion` | `IngestReading`, `ValidateReading` |
| `monitor.Analysis` | `DetectAnomaly`, `ClassifyAlert` |
| `monitor.Reporting` | `RunDiagnostics`, `GenerateSummary` |

All handler logic is deterministic — runs fully offline.

Discovered by the Facetwork runner via the `facetwork.domains` entry point
declared in `pyproject.toml`. After `pip install -e .`, Facetwork's
`fw runner start --domain sensor-monitoring` and `fw ffl seed`
pick this package up automatically.

## Install

```bash
git clone https://github.com/rlemke/fwh_sensor_monitoring.git ~/fw_handlers/fwh_sensor_monitoring
cd ~/fw_handlers/fwh_sensor_monitoring
pip install -e .
```

## Run from a Facetwork checkout

```bash
fw ffl seed --include sensor-monitoring           # one-time, seeds FFL
fw runner start --domain sensor-monitoring -- --log-format text
```

## Run a single operation from the command line

Every event facet has a matching CLI under `src/sensor_monitoring/tools/`,
backed by the same `tools/_lib/sensor.py` module the FFL handlers call:

```bash
src/sensor_monitoring/tools/ingest-reading.sh --sensor-id temp-001 --value 22.4 --unit celsius
src/sensor_monitoring/tools/validate-reading.sh --reading '{"sensor_id":"temp-001","value":22.4,"unit":"celsius"}'
src/sensor_monitoring/tools/detect-anomaly.sh --reading '{"value":120}' --baseline '{"mean":22.5,"std":1.2}'
src/sensor_monitoring/tools/classify-alert.sh --anomaly '{"is_anomaly":true,"severity":0.8}'
src/sensor_monitoring/tools/run-diagnostics.sh --sensor-id temp-001
src/sensor_monitoring/tools/generate-summary.sh --readings-json '[{"value":22.4},{"value":22.6}]'
```

The CLIs print the function's result as JSON on stdout, with a
human-readable summary on stderr.

## Layout

```
fwh_sensor_monitoring/
├── pyproject.toml                  # facetwork.domains entry point
├── README.md
├── CLAUDE.md                       # guidance for Claude Code in this repo
├── USER_GUIDE.md                   # human-facing walkthrough
├── agent-spec/                     # tools-pattern, cache-layout specs
├── agent.py                        # standalone AgentPoller variant
├── agent_registry.py               # standalone RegistryRunner entry
├── conftest.py                     # pytest fixtures
├── tests/                          # repo-level integration tests
└── src/sensor_monitoring/
    ├── __init__.py                 # exports `domain: DomainPackage`
    ├── handlers/                   # 3 event-facet subpackages + shared/ shim
    │   ├── ingestion/              # IngestReading, ValidateReading
    │   ├── analysis/               # DetectAnomaly, ClassifyAlert
    │   ├── reporting/              # RunDiagnostics, GenerateSummary
    │   └── shared/sensor_utils.py  # shim into tools/_lib/sensor
    ├── ffl/                        # monitor.ffl
    └── tools/
        ├── _lib/sensor.py          # 6 deterministic-stub functions
        ├── *.py                    # one CLI per public function
        └── *.sh                    # shell wrappers
```

## License

Apache 2.0 — see `LICENSE`.
