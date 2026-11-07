---
execution_id: 2026_11_06_23_47_02_LAUGHING_NOETHER_SGYG23_REVIEW
prompt_id: PROMPT(AD_HOC:LAUGHING_NOETHER_SGYG23_REVIEW)[2026-11-06T23:42:21+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/taurworks/pull/115
commit: e1da97588536b43f79a3501d7f135ea8d293bd0e
created_at: 2026-11-06T23:47:02+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/115
session_transcript: claude-app:886ad668-3050-4ae4-8925-4fa068b6791c
---

# Summary

Addressed 3 open review threads on PR #115 (design + work item for
accepting a symlinked `working_dir` outside `project_root`), all from
`copilot-pull-request-reviewer` on head `0e76348`, all real. Run inline as
the review-response link of a `/lrh-land` chain. `rerun_of` is empty: this
PR has no primary implementation record (the land run uses the backfill
path), and no prior `_REVIEW` record existed for this slug.

# Result

- copilot-pull-request-reviewer (`config_model.md`) — "Ordinary missing
  directories are supported ... Treating all nonexistent targets as errors
  ... would break these workflows." Confirmed real:
  `relative_working_dir_metadata` returns `is_dir()` as a bool rather than
  raising, so metadata-only create and `activate --print` accept a missing
  path. Fixed by stating that per-command missing-directory policy is
  unchanged and that only a dangling or looping symlink component becomes
  a hard error at every call site.
- copilot-pull-request-reviewer (WI) — "an in-root path such as
  `repo/../repo` is accepted ... tightens compatibility instead of
  preserving behavior exactly as today." Confirmed real: both helpers
  resolve before checking containment. Fixed by documenting rejection of
  every `..` as a deliberate tightening (necessary under lexical
  containment, since `link/..` refers to the symlink target's parent),
  removing the "unchanged" claims from acceptance and `config_model.md`,
  adding an in-root `..` test requirement, and recording the cwd-relative
  `working-dir set DIR` mapping as an Open Question in the WI.
- copilot-pull-request-reviewer (WI) — "`create_working_dir_metadata_target()`
  then resolves the path and calls `mkdir()` ... would create the missing
  external target." Confirmed real. Fixed by adding a required explicit
  invalid-symlink check before the `--create-working-dir` `mkdir`, plus a
  regression test, while preserving ordinary missing-directory creation.
  Verified on Python 3.11.8 while fixing: `Path.is_dir()` returns `False`
  for both a dangling link and a loop, and non-strict `Path.resolve()`
  raises `RuntimeError` (not `OSError`) on a loop; both facts are now in
  the WI so the implementation does not rely on existing `OSError`
  handling.

No comments skipped.

# Validation

- Tool versions: Python 3.11.8, black 26.3.1, ruff 0.15.12
- `scripts/format --check --diff`: 33 files unchanged, pass
- `scripts/lint`: all checks passed
- `scripts/test`: 350 tests, OK
- `lrh validate`: 3 errors, 10 warnings — identical to a `origin/master`
  snapshot (pre-existing YAML parse errors in
  `WI-LEGACY-CONDA-GATING-0001.md` and two July execution records, none
  touched by this PR)

# Follow-up

- `/lrh-confirm-fixes` (next link in the land chain) verifies these fixes
  against the diff and resolves the three threads.
- The WI's Open Question (cwd-relative `working-dir set DIR` mapping) is
  decided as part of implementing `WI-WORKING-DIR-SYMLINK-ESCAPE-0001`.
