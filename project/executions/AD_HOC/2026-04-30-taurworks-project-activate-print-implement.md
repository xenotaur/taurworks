---
prompt_id: "PROMPT(TAURWORKS_PROJECT_ACTIVATE_PRINT)[IMPLEMENT/2026-04-30]"
work_item: "AD_HOC"
slug: "taurworks-project-activate-print-implement"
status: "landed"
date: "2026-04-30"
---

# Summary
Implemented `taurworks project activate [PATH_OR_NAME] --print` as a safe, read-only shell-integration slice that resolves a project and prints activation guidance without mutating shell state.

# Result
- Added `project activate` under the `taurworks project` namespace with required `--print` gating for this non-mutating slice.
- Added activation-print diagnostics/formatter in shared resolution logic to reuse existing project-target resolution behavior and `.taurworks` metadata detection.
- Added CLI tests covering read-only output, required `--print` enforcement, and no filesystem mutation during `project activate --print`.
- Updated README command documentation to describe read-only behavior and explicit future wrapper requirement for shell mutation.

# Validation
- Checked prior executions for this prompt ID in `project/executions/` (none found).
- Attempted `python -m pip install -e .` (failed: environment package index could not provide `setuptools>=64` due to repeated 403 tunnel failures).
- Ran `PYTHONPATH=src python -m taurworks.cli project where` (pass).
- Ran `PYTHONPATH=src python -m taurworks.cli project list` (pass).
- Ran `PYTHONPATH=src python -m taurworks.cli project activate --print` (pass).
- Ran `PYTHONPATH=src python -m taurworks.cli project create test_project_dir` (pass).
- Ran `PYTHONPATH=src python -m taurworks.cli project activate test_project_dir --print` (pass).
- Ran `scripts/format --check` (failed, then auto-formatted file via script).
- Ran `scripts/lint` (pass).
- Ran `scripts/test` (pass).
- Attempted `scripts/prompts/record-execution --help` (failed: script not present in repository); created this execution record manually for traceability.

# Follow-up
- Add `scripts/prompts/record-execution` and `project/executions/README.md` (or update docs) to align prompt workflow instructions with actual repository contents.
