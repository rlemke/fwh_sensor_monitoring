#!/usr/bin/env python3
"""validate-reading — apply a sensor's calibration config to a reading."""

from __future__ import annotations

import argparse
import json
import sys

from sensor_monitoring.tools._lib.sensor import validate_reading


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("--reading", required=True, help="SensorReading JSON")
    p.add_argument(
        "--sensor-config",
        default=None,
        dest="sensor_config",
        help="Sensor calibration config JSON (omit for default calibration)",
    )
    args = p.parse_args()

    reading = json.loads(args.reading)
    cfg = json.loads(args.sensor_config) if args.sensor_config else None
    print(f"validate_reading: sensor={reading.get('sensor_id', '?')}", file=sys.stderr)
    valid, calibrated = validate_reading(reading, cfg)
    json.dump({"valid": valid, "calibrated_value": calibrated}, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
