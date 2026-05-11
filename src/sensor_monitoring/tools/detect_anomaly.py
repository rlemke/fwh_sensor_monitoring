#!/usr/bin/env python3
"""detect-anomaly — flag a reading against low/high + critical thresholds."""

from __future__ import annotations

import argparse
import json
import sys

from sensor_monitoring.tools._lib.sensor import detect_anomaly


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("--reading", required=True, help="SensorReading JSON")
    p.add_argument("--threshold-low", type=float, default=10.0, dest="threshold_low")
    p.add_argument("--threshold-high", type=float, default=40.0, dest="threshold_high")
    p.add_argument("--critical-low", type=float, default=-10.0, dest="critical_low")
    p.add_argument("--critical-high", type=float, default=60.0, dest="critical_high")
    args = p.parse_args()

    reading = json.loads(args.reading)
    print(
        f"detect_anomaly: value={reading.get('value', '?')} "
        f"thresholds=[{args.threshold_low}, {args.threshold_high}]",
        file=sys.stderr,
    )
    result = detect_anomaly(
        reading,
        args.threshold_low,
        args.threshold_high,
        args.critical_low,
        args.critical_high,
    )
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
