"""Sensor Monitoring — AgentPoller entry point (legacy/alternative).

For the recommended approach, use agent_registry.py which uses RegistryRunner.

Usage:
    PYTHONPATH=src python agent.py     # from the repo root
"""

from __future__ import annotations

from facetwork.runtime.agent_poller import AgentPoller, AgentPollerConfig
from sensor_monitoring.handlers import register_all_handlers


def main() -> None:
    """Start the AgentPoller with all sensor monitoring handlers."""
    poller = AgentPoller(config=AgentPollerConfig(service_name="sensor-monitoring"))
    register_all_handlers(poller)
    print("Sensor monitoring AgentPoller started")
    poller.run()


if __name__ == "__main__":
    main()
