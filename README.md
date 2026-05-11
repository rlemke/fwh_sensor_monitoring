# sensor-monitoring

A standalone [Facetwork](https://github.com/rlemke/facetwork) example package
that ingests, validates, analyzes, and reports on time-series sensor
readings using six event facets backed by a small deterministic-stub
library.

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

Discovered by the Facetwork runner via the `facetwork.examples` entry point
declared in `pyproject.toml`. After `pip install -e .`, Facetwork's
`scripts/start-runner --example sensor-monitoring` and `scripts/seed-examples`
pick this package up automatically.

## Install

```bash
git clone https://github.com/rlemke/fwh_sensor_monitoring.git ~/fw_handlers/fwh_sensor_monitoring
cd ~/fw_handlers/fwh_sensor_monitoring
pip install -e .
```

## Run from a Facetwork checkout

```bash
scripts/seed-examples --include sensor-monitoring           # one-time, seeds FFL
scripts/start-runner --example sensor-monitoring -- --log-format text
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
├── pyproject.toml                  # facetwork.examples entry point
├── README.md
├── CLAUDE.md                       # guidance for Claude Code in this repo
├── USER_GUIDE.md                   # human-facing walkthrough
├── agent-spec/                     # tools-pattern, cache-layout specs
├── agent.py                        # standalone AgentPoller variant
├── agent_registry.py               # standalone RegistryRunner entry
├── conftest.py                     # pytest fixtures
├── tests/                          # repo-level integration tests
└── src/sensor_monitoring/
    ├── __init__.py                 # exports `example: ExamplePackage`
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
