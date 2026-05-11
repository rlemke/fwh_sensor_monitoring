#!/usr/bin/env bash
# Shell wrapper for generate_summary.py — see python file for argparse help.
exec python3 "$(dirname "$0")/generate_summary.py" "$@"
