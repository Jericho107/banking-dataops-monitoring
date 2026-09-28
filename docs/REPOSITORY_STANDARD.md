# Engineering Standard

This repository follows the Pretoria BI public-evidence standard.

## Evidence standard

A technical claim should expose:

- implementation;
- reproducible execution path;
- automated or inspectable evidence;
- known limitations;
- a reverse test when the claim is materially important.

## Repository standard

Expected characteristics:

- business/control question stated before implementation detail;
- clear architecture;
- deterministic or documented data source;
- structured Python where Python is used;
- explicit SQL where SQL is material;
- tests for meaningful failure modes;
- CI for repeatable validation;
- no credentials or private operational data;
- documentation that matches executable commands;
- no unsupported production-readiness claims.

## Review checklist

Before officialisation:

- [ ] README claims match implementation;
- [ ] reverse test covers the central claim;
- [ ] `ruff check .` passes;
- [ ] `pytest` passes;
- [ ] full CI pipeline passes;
- [ ] data boundary is explicit;
- [ ] architecture matches actual runtime flow;
- [ ] stale/generated evidence is removed;
- [ ] links render correctly;
- [ ] known limitations are documented.
