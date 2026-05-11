#!/usr/bin/env bash
# Shell wrapper for classify_alert.py — see python file for argparse help.
exec python3 "$(dirname "$0")/classify_alert.py" "$@"
