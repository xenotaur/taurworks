---
prompt_id: "PROMPT(TAURWORKS_PROJECT_REFRESH)[IMPLEMENT/2026-04-27]"
work_item: "AD_HOC"
slug: "taurworks-project-refresh-implement"
status: "landed"
date: "2026-04-29"
---

# Summary
Implemented `taurworks project refresh [PATH_OR_NAME]` as a safe, idempotent scaffold repair command focused on Taurworks-owned metadata.

# Result
- Added `project refresh` subcommand under `taurworks project` with optional target argument.
- Added refresh resolution/diagnostics logic that creates only missing target directory metadata (`.taurworks/`) and `.taurworks/config.toml`.
- Enforced non-overwrite behavior: existing config file is detected and preserved.
- Added summary output sections for found, missing, created, skipped, warnings, plus a no-changes-needed signal.
- Added targeted tests for creation, non-overwrite behavior, and idempotence.
- Updated README command-model docs to include the new safe refresh behavior.

# Validation
- Attempted `python -m pip install -e .` (failed: environment cannot fetch build dependency `setuptools>=64` due 403 on package index).
- Ran `python -m taurworks.cli project refresh` (pass via source-layout execution during tests).
- Ran `python -m taurworks.cli project where` (pass via source-layout execution during tests).
- Ran `python -m taurworks.cli project list` (pass via source-layout execution during tests).
- Ran `scripts/test` (pass).
- Ran `scripts/format` (pass).
- Ran `scripts/lint` (pass after formatting).
- Attempted `scripts/prompts/record-execution ...` (failed: script not present in repository; manual execution record created).

# Follow-up
- Add the missing `scripts/prompts/record-execution` helper and referenced `project/executions/README.md` to align docs/process tooling with repository state.
