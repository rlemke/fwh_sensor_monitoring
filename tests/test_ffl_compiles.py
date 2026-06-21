"""Every shipped .ffl must parse AND validate clean (offline, no Mongo/network).

Regression guard: a workflow once referenced a step (`classify`) that was scoped
inside a nested `andThen` block, so it validated with an "undefined step" error
while still parsing — the manifest test (which only parses) didn't catch it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from facetwork.parser import FFLParser
from facetwork.source import CompilerInput, FileOrigin, SourceEntry
from facetwork.validator import validate

_FFL = sorted(
    p for p in (Path(__file__).resolve().parents[1] / "src").rglob("*.ffl")
    if "test" not in p.parts and "fixtures" not in p.parts
)


def test_ffl_files_discovered():
    assert _FFL, "no .ffl files found under src/"


@pytest.mark.parametrize("path", _FFL, ids=lambda p: p.name)
def test_ffl_validates_clean(path):
    entries = [SourceEntry(text=path.read_text(), origin=FileOrigin(path=str(path)), is_library=False)]
    entries += [
        SourceEntry(text=q.read_text(), origin=FileOrigin(path=str(q)), is_library=True)
        for q in _FFL if q != path
    ]
    ast, _ = FFLParser().parse_sources(
        CompilerInput(primary_sources=[entries[0]], library_sources=entries[1:])
    )
    errors = list(validate(ast).errors or [])
    assert not errors, f"{path.name} has validator errors: {errors}"
