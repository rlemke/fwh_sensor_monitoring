#!/usr/bin/env bash
# Shell wrapper for ingest_reading.py — see python file for argparse help.
exec python3 "$(dirname "$0")/ingest_reading.py" "$@"
