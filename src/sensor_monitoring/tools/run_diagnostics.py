#!/usr/bin/env python3
"""run-diagnostics — assemble a DiagnosticReport for a sensor."""

from __future__ import annotations

import argparse
import json
import sys

from sensor_monitoring.tools._lib.sensor import run_diagnostics


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("--sensor-id", required=True, dest="sensor_id")
    p.add_argument(
        "--anomaly",
        required=True,
        dest="anomaly_result",
        help="Anomaly result JSON",
    )
    p.add_argument("--reading", required=True, help="SensorReading JSON")
    args = p.parse_args()

    anomaly = json.loads(args.anomaly_result)
    reading = json.loads(args.reading)
    print(f"run_diagnostics: sensor={args.sensor_id}", file=sys.stderr)
    result = run_diagnostics(args.sensor_id, anomaly, reading)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
