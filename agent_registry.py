"""Sensor Monitoring — RegistryRunner entry point (RECOMMENDED).

This is the primary way to run the sensor monitoring agent.
It uses RegistryRunner to auto-load handlers from DB registrations.

Usage:
    PYTHONPATH=src python agent_registry.py     # from the repo root
"""

from __future__ import annotations

from facetwork.runtime.registry_runner import create_registry_runner
from sensor_monitoring.handlers import register_all_registry_handlers


def main() -> None:
    """Start the RegistryRunner with all sensor monitoring handlers."""
    runner = create_registry_runner("sensor-monitoring")
    register_all_registry_handlers(runner)
    print(
        f"Sensor monitoring RegistryRunner started with {len(runner.registered_names())} handlers"
    )
    runner.start()


if __name__ == "__main__":
    main()
