#!/usr/bin/env python3
"""classify-alert — derive an alert priority + payload from an anomaly result."""

from __future__ import annotations

import argparse
import json
import sys

from sensor_monitoring.tools._lib.sensor import classify_alert


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("--anomaly", required=True, help="Anomaly result JSON (from detect-anomaly)")
    p.add_argument("--sensor-id", required=True, dest="sensor_id")
    p.add_argument(
        "--override-config",
        default=None,
        dest="override_config",
        help="Optional priority override config JSON",
    )
    args = p.parse_args()

    anomaly = json.loads(args.anomaly)
    override = json.loads(args.override_config) if args.override_config else None
    print(f"classify_alert: sensor={args.sensor_id}", file=sys.stderr)
    result = classify_alert(anomaly, args.sensor_id, override)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
