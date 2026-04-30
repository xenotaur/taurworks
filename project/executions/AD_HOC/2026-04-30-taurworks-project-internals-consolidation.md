---
prompt_id: "PROMPT(TAURWORKS_PROJECT_INTERNALS_CONSOLIDATION)[REFACTOR/2026-04-29]"
work_item: "AD_HOC"
slug: "taurworks-project-internals-consolidation"
status: "landed"
date: "2026-04-30"
---

# Summary
Consolidated shared internal logic for `taurworks project where|list|refresh|create` into a dedicated internal module while preserving command behavior and safety/idempotence semantics.

# Result
- Added `src/taurworks/project_internals.py` to centralize project target resolution, metadata root detection, project discovery, XDG config-path candidate lookup, and safe metadata scaffolding.
- Refactored `src/taurworks/project_resolution.py` to delegate shared behaviors to `project_internals` while preserving output text/command semantics.
- Added focused internal tests in `tests/project_tests/project_internals_test.py` for target resolution defaults, parent-walk metadata detection, and non-overwrite scaffolding behavior.
- Updated README with a concise implementation note that these commands now share one consolidated internal model.

# Validation
- Attempted `python -m pip install -e .` (failed: environment package index could not provide `setuptools>=64` due repeated 403 tunnel failures).
- Ran `taurworks project where` (pass).
- Ran `taurworks project list` (pass).
- Ran `taurworks project refresh` (pass).
- Ran `taurworks project create test_project_dir` (pass).
- Ran `scripts/format` (pass).
- Ran `scripts/lint` (pass).
- Ran `scripts/test` (pass).
- Attempted `scripts/prompts/record-execution --help` (failed: script not present in repository); created this execution record manually to preserve traceability.

# Follow-up
- Add the missing `scripts/prompts/record-execution` helper and referenced `project/executions/README.md` so prompt-workflow docs and repository tooling are aligned.
