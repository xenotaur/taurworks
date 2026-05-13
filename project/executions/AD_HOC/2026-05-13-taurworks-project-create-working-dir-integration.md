---
prompt_id: "PROMPT(TAURWORKS_PROJECT_CREATE_WORKING_DIR_INTEGRATION)[IMPLEMENT/2026-05-12]"
work_item: "AD_HOC"
slug: "taurworks-project-create-working-dir-integration"
status: "landed"
date: "2026-05-13"
---

# Summary
Integrated working-directory metadata into `taurworks project create`.

# Result
- Added `taurworks project create [PATH_OR_NAME] --working-dir DIR`.
- Kept create delegated to the existing `project refresh` scaffolding path before recording optional metadata.
- Recorded `paths.working_dir` as a project-root-relative path without creating the work directory.
- Rejected absolute working-directory paths and paths that escape `project_root`.
- Preserved the default create behavior when `--working-dir` is omitted so no misleading `[paths].working_dir` metadata is invented.
- Updated README/design documentation and CLI tests for create working-directory behavior.

# Validation
- Read `AGENTS.md`, `STYLE.md`, and `PROMPTS.md` before editing.
- Attempted to read `project/executions/README.md` (failed: file is not present in this repository checkout).
- Checked prior executions for this prompt ID with `rg -n "TAURWORKS_PROJECT_CREATE_WORKING_DIR_INTEGRATION|PROJECT_CREATE_WORKING_DIR|working-dir" project/executions project/work_items src tests README.md project/design -S`; no exact prior execution record was found.
- Ran `./scripts/test` (pass).
- Ran `./scripts/lint` (pass).
- Ran `./scripts/format` (pass).
- Attempted `python -m pip install -e .` (failed because build isolation could not fetch `setuptools>=64` through the environment network/proxy).
- Ran `python -m pip install --no-build-isolation -e .` (pass).
- Ran `taurworks project create TestProject --working-dir repo` in a temporary directory (pass).
- Ran `taurworks project working-dir show` from the temporary project root (pass).
- Ran `taurworks project refresh TestProject` from the temporary parent directory (pass).
- Ran `./scripts/smoke` (pass).
- Attempted `scripts/prompts/record-execution --prompt-id "PROMPT(TAURWORKS_PROJECT_CREATE_WORKING_DIR_INTEGRATION)[IMPLEMENT/2026-05-12]" --work-item AD_HOC --slug taurworks-project-create-working-dir-integration --status landed` (failed: script not present in repository); created this execution record manually following existing repository conventions.

# Follow-up
- Add or restore `scripts/prompts/record-execution` and `project/executions/README.md` so prompt-workflow instructions match repository contents.

# Review follow-up
- Addressed PR review feedback for create summaries that reported `changed: False` after writing `paths.working_dir` on an already-refreshed project.
- Replaced brittle `root_created` string matching with a pre-refresh existence check.
- Changed `set_working_dir_metadata` to skip no-op config writes and return an explicit change flag.
- Moved test config/file reads after return-code assertions so command stdout/stderr remains visible on failures.
- Added a regression test for already-refreshed projects where `create --working-dir` writes metadata and reports the config update.
