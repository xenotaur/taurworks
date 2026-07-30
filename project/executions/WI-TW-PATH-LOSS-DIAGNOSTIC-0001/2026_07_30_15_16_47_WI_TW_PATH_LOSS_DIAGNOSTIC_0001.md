---
execution_id: 2026_07_30_15_16_47_WI_TW_PATH_LOSS_DIAGNOSTIC_0001
prompt_id: PROMPT(WI-TW-PATH-LOSS-DIAGNOSTIC-0001:WI_TW_PATH_LOSS_DIAGNOSTIC_0001)[2026-07-30T15:16:47-04:00]
work_item: WI-TW-PATH-LOSS-DIAGNOSTIC-0001
status: in_progress
rerun_of:
pr: pending
commit: pending
created_at: 2026-07-30T15:16:47-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-TW-PATH-LOSS-DIAGNOSTIC-0001.md
session_transcript: claude-app:43689ae3-1b8e-45ff-b3b8-75e8997239fb
---

# Summary

Implemented `WI-TW-PATH-LOSS-DIAGNOSTIC-0001`: a Conda PATH-loss diagnostic
for the `tw` shell helper (Decision #4 of
`project/design/packaging_and_install.md`), covering all 8
`command taurworks ...` call sites in
`src/taurworks/resources/shell/taurworks-shell.sh`.

# Result

**New `_tw_require_taurworks` guard function**: checks `command -v
taurworks`; on failure, prints a diagnostic to stderr naming the likely
cause (an active Conda environment without `taurworks` installed, when
`$CONDA_DEFAULT_ENV` is set) or a generic `$PATH`/`pipx list` pointer
(when it isn't), names `tl` as an immediately-usable fallback, and returns
1 instead of letting the shell's own bare `command not found` be the only
signal.

**Two call sites, minimizing subprocess spawns:**
1. A single check at the top of `tw()`, before any dispatch -- covers 6 of
   the 8 sites in one call: `tw activate`'s own pre-Conda-activation
   `project activate --shell` calls (both branches), `tw shell refresh`'s
   `shell print` call, `tw help`'s two delegation calls, and the general
   fallthrough.
2. A second check inside `_tw_offer_legacy_trust`, which is only reached
   *after* `_tw_activate` may have already run `conda activate` --
   `taurworks` could have been resolvable at the top of the `tw`
   invocation and become unresolvable by the time this function runs, so
   it needs its own re-check rather than trusting the stale result from
   check #1. Covers the remaining 2 sites: `legacy inspect` and `project
   trust set`.

No new subprocess spawn beyond these checks: within a single function
body PATH cannot have changed since the top of that function (no `conda
activate` call happens inside `tw()`'s own body, `_tw_shell_refresh`, or
the help/fallthrough branches), so one `command -v taurworks` call per
function reused throughout.

**`tl` verified to need no equivalent change**: `src/taurworks/resources/
sourceme/aliases.source` never calls `command taurworks` at all -- it
only reads `.taurworks/config.toml`/legacy script paths directly by
design (`WI-TL-BREAKGLASS-0001`), confirmed via inspection.

**README.md**: added a "PATH-loss diagnostic" paragraph under "Shell
helper details" documenting the behavior, the Conda-switch cause, and
`tl` as the interim fallback.

**Tests** (`tests/shell_helper_test.py`, +6): a new `_path_without_taurworks()`
helper builds a `$PATH` containing only the directories needed for bash
and the handful of external tools the helper calls (`awk`, `mkdir`,
`dirname`, `readlink`, `mv`, `rm`), computed dynamically via `shutil.which`
and filtered to exclude any directory that also has a real `taurworks`
executable -- portable across the macOS/Ubuntu CI matrix, unlike a
hardcoded path list. New tests cover: the fallthrough delegation (with and
without `$CONDA_DEFAULT_ENV` set, to prove both diagnostic branches),
`tw activate` before any Conda activation, `tw shell refresh`, `tw help`,
and `_tw_offer_legacy_trust` (simulating "after conda activate switched
environments" the same way the existing tests in that class already
simulate the interactive prompt -- by calling the function directly,
since no real TTY is available in a subprocess test).

# Validation

- `git rev-parse HEAD` (pre-push, on top of `94cef92`): `24a246b9b74a6a26b91b8536b59d128650ebe4be`
- Tool versions (Taurworks conda env): Python 3.11.10, black 26.3.1, ruff 0.15.12
- `./scripts/format --check --diff` (via `black --check --diff src tests`
  directly, per `project_scripts_version_tools_missing`): 32 files
  unchanged, pass
- `./scripts/lint` (via `ruff check src tests` directly): pass
- `./scripts/test` (via `python -m unittest discover -s tests -p
  "*_test.py"`, `PYTHONPATH=src:tests`): 316 tests, OK (6 new)
- `bash -n src/taurworks/resources/shell/taurworks-shell.sh`: syntax OK
- Manual dogfood equivalent: the 6 new tests directly exercise the
  diagnostic firing at each of the 5 named entry points (fallthrough,
  `tw activate` pre-activation, `tw shell refresh`, `tw help`, and the
  post-conda-activate legacy-trust path) via a real bash subprocess with a
  constructed `$PATH` that excludes `taurworks`, standing in for a Conda
  environment switch.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- `session_transcript: pending` should be updated to
  `claude-app:<session-id>` after this session ends.
- Next steps: open PR, wait for reviewer comments, run
  `/lrh-review-response`/`/lrh-confirm-fixes`, then `/lrh-closeout` after
  merge.
