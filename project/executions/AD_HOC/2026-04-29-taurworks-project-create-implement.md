---
prompt_id: "PROMPT(TAURWORKS_PROJECT_CREATE)[IMPLEMENT/2026-04-27]"
work_item: "AD_HOC"
slug: "taurworks-project-create-implement"
status: "landed"
date: "2026-04-29"
---

# Summary
Implemented `taurworks project create [PATH_OR_NAME]` as a safe thin wrapper around `taurworks project refresh`.

# Result
- Added `project create` subcommand under `taurworks project` with optional target argument.
- Added create diagnostics/output that delegates behavior to refresh scaffolding logic.
- Preserved safety behavior: target directory is created only when missing, existing files are not overwritten, and warnings/skipped items are reported.
- Added focused tests covering create+scaffolding, no-overwrite behavior, and idempotence.
- Updated README command documentation for `taurworks project create`.

# Validation
- Attempted `python -m pip install -e .` (failed: environment cannot fetch build dependency `setuptools>=64` due 403 on package index).
- Ran `PYTHONPATH=src python -m unittest tests/project_tests/project_create_test.py tests/project_tests/project_refresh_test.py tests/project_tests/project_list_test.py tests/project_tests/project_where_test.py` (pass).
- Ran `PYTHONPATH=/workspace/taurworks/src python -m taurworks.cli project create test_dir` (pass in temporary directory).
- Ran `PYTHONPATH=/workspace/taurworks/src python -m taurworks.cli project where` (pass in temporary directory).
- Ran `PYTHONPATH=/workspace/taurworks/src python -m taurworks.cli project list` (pass in temporary directory).
- Attempted `scripts/prompts/record-execution ...` (failed: script not present in repository; manual execution record created).

# Follow-up
- Add missing prompt helper tooling (`scripts/prompts/record-execution`) and `project/executions/README.md` so documented process matches repository state.
