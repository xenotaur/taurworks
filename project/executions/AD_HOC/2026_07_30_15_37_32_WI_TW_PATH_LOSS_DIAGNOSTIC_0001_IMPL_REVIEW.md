---
execution_id: 2026_07_30_15_37_32_WI_TW_PATH_LOSS_DIAGNOSTIC_0001_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_TW_PATH_LOSS_DIAGNOSTIC_0001_IMPL_REVIEW)[2026-07-30T15:37:32-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_07_30_15_16_47_WI_TW_PATH_LOSS_DIAGNOSTIC_0001
pr: https://github.com/xenotaur/taurworks/pull/94
commit: pending
created_at: 2026-07-30T15:37:32-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/94
session_transcript: claude-app:43689ae3-1b8e-45ff-b3b8-75e8997239fb
---

# Summary

Addressed 2 open review comments on PR #94 (`WI-TW-PATH-LOSS-DIAGNOSTIC-0001`
implementation), both from `chatgpt-codex-connector`, both real bugs.

# Result

- chatgpt-codex-connector (P2) — "Resolve only executable PATH entries."
  Confirmed real: bash's `command -v taurworks` succeeds (exit 0) for a
  shell function or alias named `taurworks`, printing just the bare name
  rather than a path, but the later `command taurworks ...` call sites use
  the `command` builtin, which explicitly bypasses function/alias lookup.
  A function-only match would have passed the guard and still hit a bare
  `command not found` at the real call site -- the exact failure this
  diagnostic exists to replace. Fixed by extracting a new
  `_tw_taurworks_executable_path` helper that only accepts an absolute
  path that is also a regular, executable file (`case "$resolved" in /*)`
  plus `[ -f ] && [ -x ]`), and having `_tw_require_taurworks` call that
  instead of a bare `command -v` exit-status check.
- chatgpt-codex-connector (P2) — "Point the diagnostic to a valid
  installation source." Confirmed real: the diagnostic's Conda-branch
  message suggested `pipx install taurworks` / `pip install taurworks`,
  but `taurworks` is not published to PyPI (per README.md) -- both would
  query a package index and fail for the user following the diagnostic,
  and `pipx install` doesn't install into the active Conda environment
  anyway. Reworded to point at `scripts/install` from a checkout or
  `pipx install <path-to-checkout>`, matching the actual documented
  install path.

Added a regression test for the function/alias-bypass fix
(`test_tw_prints_diagnostic_when_taurworks_is_only_a_shell_function`:
defines a shell function named `taurworks` with no real executable on
`$PATH`, confirms the diagnostic still fires instead of a bare `command
not found`) and extended the existing conda-branch diagnostic test with
assertions that the corrected message no longer suggests a bare-name
`pipx`/`pip install taurworks` and does mention `scripts/install`.

No comments skipped.

# Validation

- Tool versions (Taurworks conda env): Python 3.11.10, black 26.3.1, ruff 0.15.12
- `black --check --diff src tests`: 32 files unchanged, pass
- `ruff check src tests`: pass
- `python -m unittest discover -s tests -p "*_test.py"` (`PYTHONPATH=src:tests`):
  317 tests, OK (1 new since the implementation commit)
- `bash -n src/taurworks/resources/shell/taurworks-shell.sh`: syntax OK
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- `session_transcript: pending` should be updated to
  `claude-app:<session-id>` after this session ends.
- Recommend `/lrh-confirm-fixes` before merge to verify the fixes against
  the current diff and resolve the review threads.
