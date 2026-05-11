# sensor-monitoring tools

CLI utilities for every event facet the sensor-monitoring example
exposes. Each operation has:

- a pure-function stub under `_lib/sensor.py` (the single source of truth),
- a CLI script `<verb>_<noun>.py` that argparse-parses input and prints JSON,
- a thin shell wrapper `<verb>-<noun>.sh`.

The FFL handlers in `src/sensor_monitoring/handlers/` call into the
same `_lib/sensor.py` via `handlers/shared/sensor_utils.py`, so both
surfaces share one implementation.

## CLI map

| CLI | FFL facet | `_lib` function |
|-----|-----------|-----------------|
| `ingest-reading.sh` | `monitor.Ingestion.IngestReading` | `ingest_reading` |
| `validate-reading.sh` | `monitor.Ingestion.ValidateReading` | `validate_reading` |
| `detect-anomaly.sh` | `monitor.Analysis.DetectAnomaly` | `detect_anomaly` |
| `classify-alert.sh` | `monitor.Analysis.ClassifyAlert` | `classify_alert` |
| `run-diagnostics.sh` | `monitor.Reporting.RunDiagnostics` | `run_diagnostics` |
| `generate-summary.sh` | `monitor.Reporting.GenerateSummary` | `generate_summary` |

## Conventions

- Help: `<cli>.sh --help` — every CLI uses argparse.
- Stderr: one-line human summary mirroring the FFL step log.
- Stdout: pretty-printed JSON dict (the same shape the FFL handler emits).
- Exit code: 0 on success, non-zero on argparse error.
- Imports: every CLI uses `from sensor_monitoring.tools._lib.sensor import …`.
- Stubs are deterministic — same input, same output (hashlib-based, no
  clock / random / I/O).

## Example: minimal pipeline from the shell

```bash
# 1. Ingest a reading (first one, no last_reading)
R=$(src/sensor_monitoring/tools/ingest-reading.sh \
      --sensor-id temp-001 --value 22.4 --unit celsius)
READING=$(echo "$R" | jq '.reading')

# 2. Validate it against default calibration
src/sensor_monitoring/tools/validate-reading.sh --reading "$READING"

# 3. Check for anomalies
A=$(src/sensor_monitoring/tools/detect-anomaly.sh --reading "$READING")

# 4. Classify the alert
ALERT=$(src/sensor_monitoring/tools/classify-alert.sh \
          --sensor-id temp-001 --anomaly "$A")

# 5. Diagnostics + summary
D=$(src/sensor_monitoring/tools/run-diagnostics.sh \
      --sensor-id temp-001 --anomaly "$A" --reading "$READING")
src/sensor_monitoring/tools/generate-summary.sh \
  --sensor-id temp-001 --diagnostic "$D" --alert "$ALERT"
```

## Adding a new tool

1. Add a pure-function stub to `_lib/sensor.py` (or a new
   `_lib/<domain>.py` module). Keep it deterministic — hashlib /
   stdlib only, no time-of-day, no `random`.
2. Re-export the symbol from
   `src/sensor_monitoring/handlers/shared/sensor_utils.py`.
3. Copy an existing CLI here as a template; adjust argparse + the
   function call.
4. Create the matching `.sh` wrapper + `chmod +x`.
5. If the new function corresponds to an FFL facet, wire it through
   the matching handler module's `_DISPATCH`.
