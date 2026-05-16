---
prompt_id: "PROMPT(TAURWORKS_PROJECT_REGISTRY)[IMPLEMENT/2026-05-15]"
work_item: "AD_HOC"
slug: "taurworks-project-registry"
status: "landed"
date: "2026-05-16"
---

# Summary
Implemented Phase 1b global project registry commands for explicit registration of projects outside normal workspace discovery.

# Result
- Added `taurworks project register NAME PATH`, `taurworks project unregister NAME`, and `taurworks project registry list`.
- Stored registry entries in global XDG config as `[projects.NAME].root`.
- Added duplicate-name protection with `--force`, missing-path protection with `--allow-missing`, project-local config warnings, and workspace child collision visibility.
- Updated README documentation for registry purpose, commands, storage, safety, collision policy, and later activation-resolution scope.
- Added unit and CLI tests for registry writes/removal/listing, missing paths, duplicates, and workspace collisions.

# Validation
- PASS: `rg -n "PROMPT\\(TAURWORKS_PROJECT_REGISTRY\\)\\[IMPLEMENT/2026-05-15\\]" project/executions || true` found no prior execution record before implementation.
- BLOCKED: `python -m pip install -e .` failed because isolated build dependency fetching for `setuptools>=64` was blocked by a 403 proxy response.
- PASS: `./scripts/develop` installed the project in editable mode with `--no-build-isolation` and constrained dev dependencies.
- PASS: Manual registry validation with temporary `XDG_CONFIG_HOME`, `taurworks workspace set`, `taurworks project register`, `taurworks project registry list`, `taurworks project unregister`, and a final registry list.
- PASS: `./scripts/format --check --diff`.
- PASS: `./scripts/lint`.
- PASS: `./scripts/test`.
- PASS: `./scripts/smoke`.
- BLOCKED: `scripts/prompts/record-execution --prompt-id "PROMPT(TAURWORKS_PROJECT_REGISTRY)[IMPLEMENT/2026-05-15]" --work-item AD_HOC --slug taurworks-project-registry --status landed` because `scripts/prompts/record-execution` is not present in this checkout; this record was created manually following `project/executions/README.md`.

# Follow-up
Wire global activation resolution to consult the registry in a later phase.
