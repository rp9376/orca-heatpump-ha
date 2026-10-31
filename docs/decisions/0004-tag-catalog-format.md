# 0004. Tag catalog as typed Python

Status: Accepted (user, 2026-10-31)

## Context
The old integration keeps its tags in YAML, loaded with PyYAML, aiofiles and
pydantic at runtime. The new catalog describes a few hundred tags: name per
circuit slot, kind, scale, unit, writability, range and enum maps.

## Decision
The catalog is Python: frozen dataclasses in `client/catalog.py`.

## Consequences
- mypy checks every entry; no runtime YAML, pydantic or aiofiles, and fast
  import.
- Contributors edit Python instead of YAML; `CONTRIBUTING.md` explains
  adding a tag.
- A unit test checks the catalog against `research/moja_orca_catalog.json`
  (types, ranges, enum orders) wherever that file has the tag.
