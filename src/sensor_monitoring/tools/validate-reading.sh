#!/usr/bin/env bash
# Shell wrapper for validate_reading.py — see python file for argparse help.
exec python3 "$(dirname "$0")/validate_reading.py" "$@"
