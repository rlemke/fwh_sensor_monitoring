#!/usr/bin/env python3
"""ingest-reading — create a SensorReading and report its quality.

Wraps :func:`sensor_monitoring.tools._lib.sensor.ingest_reading`.
``--last-reading`` is optional JSON; omit it for the first reading on a
new sensor (the stub returns ``quality="initial"``).
"""

from __future__ import annotations

import argparse
import json
import sys

from sensor_monitoring.tools._lib.sensor import ingest_reading


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("--sensor-id", required=True, dest="sensor_id")
    p.add_argument("--value", type=float, required=True)
    p.add_argument("--unit", default="celsius")
    p.add_argument(
        "--last-reading",
        default=None,
        dest="last_reading",
        help="Previous reading as JSON, or omit for the first reading",
    )
    args = p.parse_args()

    last = json.loads(args.last_reading) if args.last_reading else None
    print(f"ingest_reading: sensor={args.sensor_id} value={args.value}{args.unit}", file=sys.stderr)
    reading, quality = ingest_reading(args.sensor_id, args.value, args.unit, last)
    json.dump({"reading": reading, "quality": quality}, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
