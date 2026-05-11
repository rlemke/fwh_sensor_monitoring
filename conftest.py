"""Root conftest for the sensor-monitoring repo.

The package is installed editable (``pip install -e .``) so handler
modules resolve via the standard ``sensor_monitoring.handlers.*`` path —
no ``sys.path`` gymnastics required.
"""

from __future__ import annotations
