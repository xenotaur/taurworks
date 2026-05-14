---
prompt_id: "PROMPT(TAURWORKS_PROJECT_INIT)[IMPLEMENT/2026-05-13]"
work_item: "AD_HOC"
slug: "taurworks-project-init-implement"
status: "landed"
date: "2026-05-14"
---

# Summary
Implemented `taurworks project init [PATH] [--working-dir DIR] [--create-working-dir]` as the safe, idempotent existing-root initialization command.

# Result
- Added the `project init` CLI subcommand for initializing the current directory or an explicit existing path as a Taurworks project root.
- Reused existing refresh/config scaffolding internals for `.taurworks/` metadata creation and repair.
- Added working-directory validation that rejects absolute paths and escaping paths, requires existing directories by default, and creates missing directories only with `--create-working-dir`.
- Preserved `project create` behavior except for sharing existing helpers where appropriate.
- Updated README documentation for implemented `project init` behavior and the remaining planned `project create` refinements.
- Added CLI tests covering current-directory init, explicit-path init, idempotence, working-directory metadata, missing working-directory failure, explicit working-directory creation, path rejection, and file preservation.

# Validation
- Read `AGENTS.md`, `STYLE.md`, `PROMPTS.md`, and `project/executions/README.md` before editing.
- Checked prior executions for this prompt ID with `rg -n "PROMPT\\(TAURWORKS_PROJECT_INIT\\)\\[IMPLEMENT/2026-05-13\\]|TAURWORKS_PROJECT_INIT|project init" project/executions src tests README.md docs 2>/dev/null || true`; no exact prior execution record was found.
- Ran `./scripts/format` (pass after applying Black formatting).
- Ran `./scripts/test` (pass).
- Ran `./scripts/lint` (pass).
- Attempted `python -m pip install -e .` (failed because build isolation could not fetch `setuptools>=64` through the environment network/proxy).
- Ran `python -m pip install --no-build-isolation -e .` (pass).
- Ran `taurworks project init --working-dir test_repo --create-working-dir` from `/tmp/taurworks-init-demo/TestProject` (pass).
- Ran `taurworks project working-dir show` from `/tmp/taurworks-init-demo/TestProject` (pass).
- Ran `taurworks project activate --print` from `/tmp/taurworks-init-demo/TestProject` (pass).
- Attempted `scripts/prompts/record-execution --help` (failed: script not present in repository); created this execution record manually following existing repository conventions.

# Follow-up
- Add or restore `scripts/prompts/record-execution` so prompt-workflow instructions match the repository checkout.
