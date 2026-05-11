#!/usr/bin/env bash
# Shell wrapper for run_diagnostics.py — see python file for argparse help.
exec python3 "$(dirname "$0")/run_diagnostics.py" "$@"
