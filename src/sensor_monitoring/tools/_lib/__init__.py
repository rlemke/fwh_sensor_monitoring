"""Deterministic-stub implementation for the sensor-monitoring example.

``sensor`` holds the 6 pure functions that back every event facet plus
two hash-based helpers (``_hash_int``, ``_hash_float``). No clock, no
``random``, no I/O — same input, same output, every time. Swap in real
sensor APIs by replacing the stubs in :mod:`sensor`; signatures and
return shapes stay the same and the FFL handlers + CLIs pick up the
change transparently.
"""
