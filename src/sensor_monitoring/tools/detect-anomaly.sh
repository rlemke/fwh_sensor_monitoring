#!/usr/bin/env bash
# Shell wrapper for detect_anomaly.py — see python file for argparse help.
exec python3 "$(dirname "$0")/detect_anomaly.py" "$@"
