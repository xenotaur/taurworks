---
prompt_id: "PROMPT(TAURWORKS_PROJECT_ACTIVATE_WORKING_DIR_INTEGRATION)[IMPLEMENT/2026-05-12]"
work_item: "AD_HOC"
slug: "taurworks-project-activate-working-dir-integration"
status: "landed"
date: "2026-05-13"
---

# Summary
Integrated configured project working-directory metadata into `taurworks project activate --print`.

# Result
- Updated `taurworks project activate [PATH_OR_NAME] --print` to read `.taurworks/config.toml` and use `[paths].working_dir` when configured.
- Validated configured `working_dir` values as relative paths that resolve inside `project_root` before printing activation guidance.
- Printed project root, config path, configured working directory, resolved absolute working directory, existence status, a manual `cd` command, and `shell_mutation: not performed`.
- Kept the command read-only: no shell scripts are sourced, no directories are changed, no environments are activated, and no files are written.
- Added diagnostics for missing config, unconfigured `working_dir`, missing configured work directory, and invalid escaping config.
- Updated README/design documentation and CLI tests for working-directory-aware activation guidance.

# Validation
- Read `AGENTS.md`, `STYLE.md`, and `PROMPTS.md` before editing.
- Attempted to read `project/executions/README.md` (failed: file is not present in this repository checkout).
- Checked prior executions for this prompt ID with `rg -n "TAURWORKS_PROJECT_ACTIVATE_WORKING_DIR_INTEGRATION|IMPLEMENT/2026-05-12" project PROMPTS.md README.md tests src`; no exact prior execution record was found.
- Ran `python -m unittest` (warning: unittest default discovery ran zero tests in this repository layout).
- Ran `scripts/test` (pass).
- Attempted `python -m pip install -e .` (failed because build isolation could not fetch `setuptools>=64` through the environment network/proxy).
- Ran `python -m pip install -e . --no-build-isolation` (pass).
- Ran `taurworks project create TestProject --working-dir repo` in a temporary directory (pass).
- Ran `taurworks project activate TestProject --print` in the same temporary directory (pass).
- Ran `taurworks project working-dir show` from the temporary project root (pass).
- Ran `scripts/lint` (pass).
- Ran `scripts/format` (pass).
- Attempted `scripts/prompts/record-execution --prompt-id "PROMPT(TAURWORKS_PROJECT_ACTIVATE_WORKING_DIR_INTEGRATION)[IMPLEMENT/2026-05-12]" --work-item AD_HOC --slug taurworks-project-activate-working-dir-integration --status landed` (failed: script not present in repository); created this execution record manually following existing repository conventions.

# Follow-up
- Add or restore `scripts/prompts/record-execution` and `project/executions/README.md` so prompt-workflow instructions match repository contents.
- Implement actual parent-shell mutation only in a later explicit `tw activate`/shell-wrapper slice.
