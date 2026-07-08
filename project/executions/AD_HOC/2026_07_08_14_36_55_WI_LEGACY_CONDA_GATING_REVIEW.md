---
execution_id: 2026_07_08_14_36_55_WI_LEGACY_CONDA_GATING_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LEGACY_CONDA_GATING_REVIEW)[2026-07-08T14:31:34-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_07_08_13_37_09_WI_LEGACY_CONDA_GATING
pr: https://github.com/xenotaur/taurworks/pull/63
commit: 
created_at: 2026-07-08T14:36:55-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/63
session_transcript: pending
---

# Summary

Address open review comments on PR #63 (`WI-LEGACY-CONDA-GATING-0001`) via
`lrh request review_response`.

# Result

Fetched 5 open review comments, which clustered into 2 distinct issues:

**Issue A — misleading activation guidance when Conda env is skipped (3
comments: chatgpt-codex-connector, copilot-pull-request-reviewer x2)**

`refresh_project`/`create_project` still unconditionally write
`.taurworks/project-setup.source` with `conda activate {env_name}` and print
"To activate, run: source ..." even when `--create-env` was omitted, so
following the printed guidance now fails since the env was never created.

Presence: confirmed present. Validity: confirmed — real UX regression
introduced by this item's default-behavior change (previously the env always
existed, so the same guidance always worked). Feasibility: fixable without
touching the script write itself. Fixed by adding a warning print in both
`refresh_project` and `create_project` (`src/taurworks/manager.py`) when
`create_env=False`, noting the setup script still references the
(nonexistent) Conda environment and will fail until it's created or another
environment is activated manually. The setup script's own content and write
behavior are unchanged, preserving this work item's Acceptance Criteria that
`.taurworks/project-setup.source` is written "exactly as before this item."

**Issue B — `--create-env` help text overstates the default (2 comments:
copilot-pull-request-reviewer)**

The `--create-env` flag help text said the default is "metadata only," but
directories and the setup script are still created by default; only Conda
environment creation is skipped.

Presence: confirmed present. Validity: confirmed — inaccurate wording.
Feasibility: trivial. Fixed by rewording the `--create-env` help text in
`src/taurworks/cli.py` (both `create` and `refresh` subparsers) to say only
Conda environment creation is skipped by default.

No comments were skipped.

# Validation

- `git rev-parse HEAD` / `git status --short` captured before validation
- `scripts/version tools` — not present in this repo; recorded versions
  directly: Python 3.11.8, Black 26.3.1, Ruff 0.15.12
- `scripts/format --check --diff` — 24 files unchanged
- `scripts/lint` — Black + Ruff, all checks passed
- `scripts/test` — 170 tests, OK
- `lrh validate` — 4 errors / 1 warning, identical to the pre-existing
  `contributors/contributors.md` and orphaned-work-item issues noted in the
  primary execution record; no new errors introduced
- Manual smoke test: `taurworks create SmokeTest2` (no `--create-env`) prints
  the new warning referencing the unmet Conda environment; `taurworks create
  --help` shows the corrected `--create-env` wording

# Follow-up

- `session_transcript` is `pending`; update to `claude-app:<session-id>` once
  the session ID is known.
- None of the fixes here touch the Non-Goals boundary (repository-directory
  creation and the `project-setup.source` write remain unchanged); no new
  follow-up items are needed.
