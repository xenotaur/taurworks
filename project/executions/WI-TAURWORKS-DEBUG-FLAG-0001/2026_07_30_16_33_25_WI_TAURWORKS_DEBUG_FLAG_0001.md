---
execution_id: 2026_07_30_16_33_25_WI_TAURWORKS_DEBUG_FLAG_0001
prompt_id: PROMPT(WI-TAURWORKS-DEBUG-FLAG-0001:WI_TAURWORKS_DEBUG_FLAG_0001)[2026-07-30T16:33:25-04:00]
work_item: WI-TAURWORKS-DEBUG-FLAG-0001
status: in_progress
rerun_of:
pr: pending
commit: pending
created_at: 2026-07-30T16:33:25-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-TAURWORKS-DEBUG-FLAG-0001.md
session_transcript: claude-app:43689ae3-1b8e-45ff-b3b8-75e8997239fb
---

# Summary

Implemented `WI-TAURWORKS-DEBUG-FLAG-0001`: a global `--debug`/`$TAURWORKS_DEBUG`
flag gating `src/taurworks/manager.py`'s legacy top-level command narration,
plus the required audit of `cli.py`'s formatter modules (Decision #5 of
`project/design/packaging_and_install.md`).

# Result

**New `--debug` flag** on the top-level `argparse` parser
(`src/taurworks/cli.py`), plus `_env_flag_truthy`/`_debug_enabled` helpers:
`--debug` always wins when passed (argparse's `store_true` gives no way to
represent an explicit "off" via the flag itself); `$TAURWORKS_DEBUG` is
only consulted as a fallback, and is truthy for any value other than
unset/empty/`0`/`false`/`no` (case-insensitive). Threaded as a `debug`
keyword argument into `manager.create_project`/`manager.refresh_project`
(and from there into the shared `create_conda_environment` helper) from
`cli.py`'s `create`/`refresh` dispatch.

**Gated all narration in `manager.py`'s `create`/`refresh` commands**
(exactly 56 total `print()` calls existed in the file before this
change): every step-announcement print (`"Creating Conda environment..."`,
`"Creating project directory..."`, `"Updating Taurworks config..."`, the
per-change lines, `"✔ Taurworks config already up to date..."`, `"✔ Conda
environment ... already exists."`, the `"Skipping Conda environment
creation..."` + `⚠ Note` pair) now requires `debug=True`. Each command's
final actionable result line(s) stay unconditional: the create_env-
conditional success/partial-success line and the trailing `"To activate,
run: tw activate {project_name}"` line for both `create` and `refresh`;
`create_project`'s "already exists" stderr error (leading to `sys.exit(1)`)
also stays unconditional, matching the "keep the actionable result visible,
success or failure" principle.

**`activate_project` needed no change**: every line it prints already is
the command's result or failure guidance -- there is no separate
narration to gate, so no `debug` parameter was added (would be unused).

**`list_projects` needed no change**, per the WI's explicit special-case
carve-out: its entire listing output (`"No projects found."` and the
`"Available projects:"` header/rows) is the command's result, not
narration, confirmed unconditional in both branches.

**`get_conda_environments`'s two warning prints** (subprocess timeout /
generic exception fetching Conda environments) were deliberately left
unconditional, not gated: they report an actual anomaly affecting
subsequent behavior (not routine step narration), and the function is
shared with `list_projects`'s `show_details` path, which the WI does not
ask to gate at all -- gating them would make their visibility depend on
which caller reached them, which is worse than the small inconsistency of
"warnings always show." Documented here as this implementation's judgment
call for reviewers to confirm or push back on.

**`cli.py` formatter-module audit (Required Change #4, acceptance
criterion 3)**: `grep -n "print(" src/taurworks/{global_config,project_resolution,project_registry,dev,legacy}.py`
returns zero matches in all five modules -- each already follows the
"gather diagnostics dict, format to one string, `cli.py` prints it once"
pattern with no debug-shaped output mixed in. `cli.py` itself was also
checked: every one of its ~28 non-manager.py/setup_command `print(...)`
calls is exactly one `print(module.format_x_output(diagnostics))` call
per command handler (the command's full documented result), plus one
`print(..., file=sys.stderr)` error path in `_handle_shell_command`.
**Audit finding: no debug-shaped output found in any of the five
formatter modules or in `cli.py` itself; nothing gated.**

**Tests**: `tests/manager_test.py` -- updated 2 pre-existing tests whose
assumption ("Skipping Conda environment creation" always printed by
default) predated this WI, since that's now narration gated off by
default; added `test_refresh_project_debug_shows_narration` and
`test_create_project_debug_shows_narration` (`debug=True` direct calls).
`tests/cli_test.py` -- new `DebugFlagCliTest` (5 subprocess tests):
default suppresses narration, `--debug` shows it, `$TAURWORKS_DEBUG=1`
shows it, `$TAURWORKS_DEBUG=0` stays off, and `--debug` takes precedence
over a falsy `$TAURWORKS_DEBUG`.

**README.md**: documents the new flag/env var precedence, the narration
examples, that final result lines are always printed, that `activate`/
`projects` are unaffected, and explicitly distinguishes this global
`--debug` from `tw activate`'s unrelated `--verbose`/`--debug` shell-level
alias.

# Validation

- Tool versions (Taurworks conda env): Python 3.11.10, black 26.3.1, ruff 0.15.12
- `black --check --diff src tests`: 32 files unchanged, pass
- `ruff check src tests`: pass
- `python -m unittest discover -s tests -p "*_test.py"` (`PYTHONPATH=src:tests`):
  324 tests, OK (7 new: 2 in `manager_test.py`, 5 in `cli_test.py`)
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- `session_transcript: pending` should be updated to
  `claude-app:<session-id>` after this session ends.
- Next steps: open PR, wait for reviewer comments, run
  `/lrh-review-response`/`/lrh-confirm-fixes`, then `/lrh-closeout` after
  merge.
