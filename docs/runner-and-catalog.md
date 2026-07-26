# Runner registration, packaging & the capability catalog

**Entry point:** `src/sensor_monitoring/__init__.py` (`domain: DomainPackage`) ·
**Registration:** `src/sensor_monitoring/handlers/__init__.py` ·
**Agent entry points:** `agent_registry.py` (RegistryRunner, primary), `agent.py` (AgentPoller, legacy) ·
**Catalog:** `src/sensor_monitoring/catalog.yaml` + `src/sensor_monitoring/catalog.py` ·
**Packaging:** `pyproject.toml` · **Tests:** `tests/test_catalog_manifest.py`,
`tests/test_sensor_handlers.py` (`TestDispatch`, `TestAgentIntegration`)

## Overview

This spec covers how the package plugs into Facetwork and how its capabilities are
discovered: the `facetwork.domains` entry point, the two agent run modes
(RegistryRunner-first), the per-facet `_DISPATCH`/`register_handlers` wiring, and the
machine-readable `catalog.yaml` manifest that lets an LLM reuse these capabilities by
intent. It answers "how does a runner find and serve these six facets, and how does a
composer discover them?"

## How it works

**Packaging / discovery.** `pyproject.toml` declares:

```toml
[project.entry-points."facetwork.domains"]
sensor-monitoring = "sensor_monitoring:domain"
```

`src/sensor_monitoring/__init__.py` exports `domain = DomainPackage(name=
"sensor-monitoring", ffl_dir=<pkg>/ffl, register_handlers=register_all_registry_handlers)`.
After `pip install -e .`, Facetwork's `fw runner start --domain sensor-monitoring`
and `fw ffl seed` (older `scripts/start-runner --example` / `scripts/seed-examples`)
pick it up via entry-point discovery. `ffl_dir` points at `ffl/monitor.ffl` (packaged
via `[tool.setuptools.package-data]`).

**Handler registration.** `handlers/__init__.py` exposes two aggregators:

- `register_all_registry_handlers(runner)` — RegistryRunner path; calls each
  subpackage's `register_handlers(runner)`, which registers each facet name with a
  `module_uri` (`file://<abs path>`) + `entrypoint="handle"`.
- `register_all_handlers(poller)` — AgentPoller path; calls each
  `register_<ns>_handlers(poller)`, which `poller.register(facet_name, handler)`.

Each `*_handlers.py` module holds a `_DISPATCH` dict (`{qualified_facet: fn}`) and a
`handle(payload)` entrypoint that looks up `payload["_facet_name"]` and calls the
matching handler. Six facets across three `_DISPATCH` tables (2 + 2 + 2).

**Agent entry points.**

- `agent_registry.py` (**RECOMMENDED**) — `create_registry_runner("sensor-monitoring")`,
  `register_all_registry_handlers(runner)`, `runner.start()`. RegistryRunner
  auto-loads handlers from DB registrations; no polling loop to hand-write.
- `agent.py` (legacy) — `AgentPoller(config=AgentPollerConfig(...))` +
  `register_all_handlers(poller)` + `poller.run()`.

**Capability catalog.** `catalog.yaml` is a curated manifest (`version: 1`,
`package: sensor-monitoring`) with a `workflows:` section (the two entry points, each
with an intent `summary`, `tags`, and `param_schema` — for reuse-first matching à la
`fw_catalog_match`) and a `facets:` section (the six facets, each with `purpose`,
`signature`, `effect`, `cost`, `namespace` — a capability index à la
`fw_capabilities`). `catalog.py` loads it (`load_manifest()`, `workflows()`,
`facets()`, `lru_cache`d, PyYAML).

## Fan-out

**N/A — infrastructure.** Registration and discovery are process-local; fan-out is a
workflow concern ([workflows](workflows.md)).

## Data & fields

- **`catalog.yaml` workflow entries:** `qualified_name`, `summary`, `tags`,
  `entry_point: true`, `param_schema`.
- **`catalog.yaml` facet entries:** `qualified_name`, `purpose`, `signature`,
  `effect` (`pure`/`external`/`io`), `cost` (`free`/`cheap`/`moderate`/`expensive`),
  `namespace`.
- **Registration payload:** facet names are the fully-qualified
  `monitor.<Ns>.<Facet>` (asserted `startswith("monitor.")` in `TestDispatch` /
  `test_registry_runner_handler_names`).

## External libraries / binaries

- **`facetwork`** (pip) — `facetwork.domains.DomainPackage`,
  `facetwork.runtime.registry_runner.create_registry_runner`,
  `facetwork.runtime.agent_poller.AgentPoller`.
- **`PyYAML`** (pip) — `catalog.py` parses `catalog.yaml`.
No binaries.

## Facets & workflows

This feature registers/serves all six event facets and both workflows documented in
the other specs — it declares no new FFL of its own. The catalog mirrors those:
2 workflows + 6 facets, and `test_catalog_manifest.py` asserts every catalog
`qualified_name` leaf is really declared in the FFL and that each facet's `effect`/
`cost` in the manifest **matches** the `with Effect(...)` / `with Cost(...)` mixins in
`monitor.ffl` (no drift).

## Cache / output

**None.** DB registrations live in Mongo (runtime state, not this package's output);
the package writes no cache/output artifacts.

## Gotchas & notes

- **Stale "examples" naming in the human docs.** `pyproject.toml` declares the
  **`facetwork.domains`** entry point and `__init__.py` exports a **`DomainPackage`**
  named `domain`. The repo `README.md` / `CLAUDE.md` still say "facetwork.examples
  entry point" / "exports `example: ExamplePackage`" and reference the old
  `scripts/start-runner --example` / `scripts/seed-examples` commands — the code is
  the source of truth (`--domain sensor-monitoring`, `fw ffl seed`). Docstrings in
  `__init__.py` also mix "examples" prose with the correct `facetwork.domains` block.
- **RegistryRunner is primary; AgentPoller is legacy.** Prefer `agent_registry.py`.
  Both share the same `_DISPATCH` tables via different `register_*` shims, so they
  cannot drift.
- **Catalog is curated, not generated.** It is hand-maintained but guarded:
  `test_catalog_manifest.py` fails if a `qualified_name` isn't in the FFL, if
  effect/cost drift from the FFL mixins, or on duplicate/overlapping entries. Update
  `catalog.yaml` whenever you add or re-annotate a facet.

## Related specs

- [workflows](workflows.md) — the two entry points this catalog indexes and the
  RegistryRunner showcase.
- [ingestion](ingestion.md) / [analysis](analysis.md) / [reporting](reporting.md) —
  the six facets registered here.
- [tools-and-lib](tools-and-lib.md) — the CLI surface parallel to these handlers.
