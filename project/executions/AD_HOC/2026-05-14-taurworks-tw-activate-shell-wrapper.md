---
prompt_id: "PROMPT(TAURWORKS_TW_ACTIVATE_SHELL_WRAPPER)[IMPLEMENT/2026-05-14]"
work_item: "AD_HOC"
slug: "taurworks-tw-activate-shell-wrapper"
status: "landed"
date: "2026-05-14"
---

# Summary
Implemented the first explicit sourced shell wrapper for Taurworks activation.

# Result
- Added `taurworks-shell.sh`, which defines `tw` and performs current-shell directory changes only for `tw activate [PATH_OR_NAME]`.
- Kept `taurworks project activate [PATH_OR_NAME] --print` read-only and updated its note to point at explicit sourced wrappers.
- Documented manual helper sourcing, the shell mutation boundary, delegation behavior, dogfood workflow, and intentionally omitted startup-file/environment activation behavior.
- Added shell helper tests for function definition, delegation, successful activation, failure without directory mutation, missing working directories, and startup-file preservation.

# Validation
- Passed: `python -m unittest tests.shell_helper_test`
- Passed: `./scripts/test`
- Passed: `./scripts/lint`
- Warning: `python -m pip install -e .` failed because build isolation attempted to fetch build dependencies through a blocked network/proxy.
- Passed: `python -m pip install -e . --no-build-isolation`
- Passed: temporary dogfood create/print activation guidance command.
- Passed: sourced-helper dogfood command changed a controlled subshell into the configured working directory.
- Warning: `scripts/prompts/record-execution --prompt-id "PROMPT(TAURWORKS_TW_ACTIVATE_SHELL_WRAPPER)[IMPLEMENT/2026-05-14]" --work-item AD_HOC --slug taurworks-tw-activate-shell-wrapper --status landed` failed because the script is not present in this checkout; this record was created manually following `project/executions/README.md`.

# Follow-up
None.
