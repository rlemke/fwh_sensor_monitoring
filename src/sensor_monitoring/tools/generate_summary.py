#!/usr/bin/env python3
"""generate-summary — produce a MonitoringSummary from diagnostic + alert."""

from __future__ import annotations

import argparse
import json
import sys

from sensor_monitoring.tools._lib.sensor import generate_summary


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("--sensor-id", required=True, dest="sensor_id")
    p.add_argument("--diagnostic", required=True, help="DiagnosticReport JSON")
    p.add_argument("--alert", required=True, help="AlertPayload JSON")
    args = p.parse_args()

    diagnostic = json.loads(args.diagnostic)
    alert = json.loads(args.alert)
    print(f"generate_summary: sensor={args.sensor_id}", file=sys.stderr)
    result = generate_summary(args.sensor_id, diagnostic, alert)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
