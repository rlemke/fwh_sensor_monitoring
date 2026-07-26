<!-- SPEC TEMPLATE — every docs/<feature>.md follows this shape so the set reads
consistently. Delete this comment in real specs. Keep sections in this order;
omit a section only if it genuinely does not apply (say so in one line rather
than dropping the heading silently). Ground every claim in the actual FFL
docstrings / handler code / tools — do not invent behaviour. -->

# <Feature Name>

**Namespace(s):** `monitor.<ns>` · **FFL:** `src/sensor_monitoring/ffl/monitor.ffl` ·
**Handlers:** `src/sensor_monitoring/handlers/<dir>/*.py` · **Tools:** `src/sensor_monitoring/tools/<...>.py` (if any) ·
**Stubs:** `src/sensor_monitoring/tools/_lib/sensor.py`

## Overview
One or two paragraphs: what this feature is for, the request it answers, and where
it sits in the pipeline (ingest → validate → analyze → report).

## How it works
The algorithm / data flow, step by step. Name the concrete `_lib` function(s) and
the shape of the data at each hop (raw args → `SensorReading` dict → `AnomalyResult`
dict → …). Note that both surfaces (CLI + FFL handler) call the same deterministic
stub in `tools/_lib/sensor.py`.

## Fan-out
Does it fan out across the fleet? If yes: what is the fan-out unit (per-sensor), which
facet drives it (a `foreach` over what list), and why it reduces wall-clock. If it is
single-task, say "single-task — no fan-out" and why (e.g. one reading, linear pipeline).

## Data & fields
The schemas and field names this feature reads/writes — be specific
(`SensorReading{sensor_id, timestamp, value, unit}`, `AnomalyResult{is_anomaly,
severity, deviation, threshold_breached}`, threshold constants like `critical_low=-40.0`).
Name the mechanism (a Python arithmetic/threshold predicate over the reading dict, a
priority-map lookup, a hashlib-seeded deterministic value). If the feature does no
filtering, say so. (Rename this heading to "Filtering & attributes" only if the feature
truly filters/selects.)

## External libraries / binaries
Every non-stdlib dependency this feature relies on and what for. This package is
**pure-stdlib** for its sensor logic (`hashlib`, `json`); the only pip deps are
`facetwork` (runtime) and `PyYAML` (catalog loader). Distinguish a **binary**
dependency from a **pip** one; say "none — stdlib only" where that is the truth.

## Facets & workflows
The key event facets and workflows, with signatures and a one-line purpose taken
from the FFL docstrings. Mark event facets (need a handler) vs pure facets, and note
`Effect`/`Cost` mixins where present (verbatim from the `with Effect(...) /
with Cost(...)` clauses in `monitor.ffl`).

## Cache / output
The cache namespace + output artifact, if any. For this package there is **no cache
and no durable output** — handlers return dicts in memory and CLIs print JSON to
stdout; the stubs perform no disk/network I/O. Say so explicitly rather than inventing
a cache namespace.

## Gotchas & notes
Known pitfalls or non-obvious constraints (JSON-string coercion in handlers, the
`"null"` sentinel, CLI-vs-FFL default drift, deterministic-stub caveats, stale entry-
point naming) — anything a future maintainer would trip on.

## Related specs
Links to the specs this feature composes with or depends on.
