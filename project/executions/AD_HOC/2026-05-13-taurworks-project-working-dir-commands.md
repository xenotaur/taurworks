---
prompt_id: "PROMPT(TAURWORKS_PROJECT_WORKING_DIR_COMMANDS)[IMPLEMENT/2026-05-12]"
work_item: "AD_HOC"
slug: "taurworks-project-working-dir-commands"
status: "landed"
date: "2026-05-13"
---

# Summary
Implemented the minimal Taurworks project metadata schema and `taurworks project working-dir` commands.

# Result
- Added schema-versioned `.taurworks/config.toml` creation with `[project].name` defaulting to the project-root directory name.
- Added safe repair for missing schema versions and empty legacy project names when the existing config can be parsed and rewritten.
- Added `taurworks project working-dir show` to display configured `paths.working_dir` or a clear unconfigured state.
- Added `taurworks project working-dir set [DIR]` to store an existing working directory as a relative path inside `project_root`.
- Rejected absolute working-directory paths and paths that escape `project_root`.
- Updated README/design documentation and tests for the schema and commands.

# Validation
- Read `AGENTS.md`, `STYLE.md`, and `PROMPTS.md` before editing.
- Attempted to read `project/executions/README.md` (failed: file is not present in this repository checkout).
- Checked prior executions for this exact prompt ID with `rg -n "TAURWORKS_PROJECT_WORKING_DIR_COMMANDS|PROJECT_WORKING_DIR" project/executions project` (none found).
- Ran `./scripts/format` (pass).
- Ran `./scripts/lint` (pass).
- Ran `./scripts/test` (pass).
- Attempted `python -m pip install -e .` (failed because build isolation could not fetch `setuptools>=64` through the environment network/proxy).
- Ran `python -m pip install --no-build-isolation -e .` (pass).
- Ran `taurworks project refresh` (pass).
- Ran `taurworks project working-dir show` (pass).
- Ran `taurworks project working-dir set .` (pass).
- Ran `taurworks project working-dir show` again (pass).
- Ran `./scripts/smoke` (pass).
- Attempted `scripts/prompts/record-execution --prompt-id "PROMPT(TAURWORKS_PROJECT_WORKING_DIR_COMMANDS)[IMPLEMENT/2026-05-12]" --work-item AD_HOC --slug taurworks-project-working-dir-commands --status landed` (failed: script not present in repository); created this execution record manually following existing repository conventions.

# Follow-up
- Add or restore `scripts/prompts/record-execution` and `project/executions/README.md` so prompt-workflow instructions match repository contents.
- Update `taurworks project activate --print` to use configured `paths.working_dir` in a later focused PR.
