---
execution_id: 2026_11_09_05_36_39_WI_WORKING_DIR_SYMLINK_ESCAPE_0001
prompt_id: PROMPT(WI-WORKING-DIR-SYMLINK-ESCAPE-0001:WI_WORKING_DIR_SYMLINK_ESCAPE_0001)[2026-11-09T05:05:22+00:00]
work_item: WI-WORKING-DIR-SYMLINK-ESCAPE-0001
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/taurworks/pull/117
commit:
created_at: 2026-11-09T05:36:39+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-WORKING-DIR-SYMLINK-ESCAPE-0001.md
session_transcript: pending
---

# Summary

Implemented `WI-WORKING-DIR-SYMLINK-ESCAPE-0001` via `/lrh-execute`. The
`working_dir` containment check is now lexical instead of using the resolved
path, so `project_root/working_dir` may be a symlink into a work tree outside
`project_root`. Absolute values and any `..` in the literal value are
rejected, and a dangling or looping symlink is a `ProjectConfigError`. PR:
https://github.com/xenotaur/taurworks/pull/117

# Result

- `src/taurworks/project_internals.py`:
  - `relative_working_dir_metadata` rejects absolute values and any `..`
    component, and checks the literal value without resolving it.
  - `relative_working_dir` maps a cwd-relative `DIR` against the resolved
    cwd. A leading `..` steps up within the cwd, but not above
    `project_root`; a `..` after any ordinary component is rejected.
  - New `check_working_dir_symlinks` uses explicit `lstat`/`stat` and
    `errno` to detect dangling and looping links, so it doesn't depend on
    the Python version.
  - It runs inside both helpers, and so before the `--create-working-dir`
    `mkdir`.
- Every caller gets the change through the shared helpers. No caller's
  error handling changed. `legacy._normalize_cd_target`, the shell helper
  and `tl` are unchanged; `tw activate` works without changes.
- Open Question decided (with user approval at the `/lrh-execute` chain
  gate): `working-dir set DIR` keeps using the physical cwd, and `$PWD` is
  not consulted. Recorded in `project/design/config_model.md`. The
  "not yet implemented" status lines in `config_model.md` and
  `design.md:29` are flipped.
- Implementer notes from review:
  - The new `..` error keeps the "may not escape" substring, so the four
    existing cli_test assertions pass unchanged.
  - Dangling and looping links have their own messages.
  - `dev.py:61` and the `--create-working-dir` help in `cli.py` are
    reworded.
  - A valid link followed by a missing tail creates the tail inside the
    link's target. This is documented and tested.
- Plan divergence approved by the user mid-run: `tests/shell_helper_test.py`
  (for the `tw activate` end-to-end test) and two stale `README.md` lines
  were added to the touched files.
- Prior-art check: present in the WI. Readiness: prompt_ready yes.

# Validation

- `scripts/version tools`: Python 3.11.8, black 26.3.1, ruff 0.15.12
- `./scripts/format --check --diff`: pass
- `./scripts/lint`: pass
- `./scripts/test`: 368 tests, OK
- `lrh validate`: 3 errors and 10 warnings, matching the baseline. All are
  in unrelated pre-existing files.
- Manual dogfood:
  - Setup: `project_root` in a `Workspace/` directory, with `working_dir`
    a symlink to a directory under `Tempspace/`.
  - `taurworks project working-dir set working_dir` succeeded.
  - `project activate --print` reported the external `resolved_working_dir`
    with `working_dir_exists: True`.
  - `tw activate` changed directory to the external target.
  - `dev where` reported the external path.
  - With the target moved away, `activate --print` reported the dangling
    symlink as invalid metadata.
- Pre-push `/lrh-self-review` diff-mode found no correctness issues
  (`project/executions/AD_HOC/2026_11_09_05_35_27_WI_WORKING_DIR_SYMLINK_ESCAPE_0001_SELFREVIEW.md`).

# Follow-up

- After `tw activate` `cd`s into an external work tree, `taurworks dev ...`
  commands run from there don't find the project. Discovery uses the
  resolved cwd, and even the logical path inside `project_root` resolves
  outside it. Needs its own work item.
- `project/focus/current_focus.md` and `project/roadmap/roadmap.md` still
  describe this WI as proposed. They should be refreshed after closeout.
