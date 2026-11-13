---
execution_id: 2026_11_13_03_07_45_WORKING_DIR_SYMLINK_FOLLOWUPS
prompt_id: PROMPT(AD_HOC:WORKING_DIR_SYMLINK_FOLLOWUPS)[2026-11-13T03:07:39+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-11-13T03:07:45+00:00
agent: claude_app
instruction_source: 'Follow-ups from project/executions/AD_HOC/2026_11_13_02_59_55_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_CLOSEOUT_NOTE.md (PR #117/#119 deferred review points)'
session_transcript: pending
---

# Summary

Small follow-ups deferred as non-blocking during the reviews of PR #117
(WI-WORKING-DIR-SYMLINK-ESCAPE-0001) and PR #119
(WI-WORKING-DIR-REVERSE-DISCOVERY-0001), both resolved.

# Result

- `project/design/config_model.md` ("Discovery from inside a symlinked work
  tree") and the README document that a `working_dir` linked to a broad
  directory (e.g. `$HOME`) claims every directory under it with no
  `.taurworks/` in it or above it, including `dev test` using that project's
  `[dev.commands]` and running in the link's target. Checked by hand in a
  scratch layout (an unrelated clone under the broad target resolved by
  `working_dir_reverse_lookup`, and `dev test` ran the override in the
  target).
- `AMBIGUITY_GUIDANCE` in `src/taurworks/project_internals.py`: "rerun" is
  now just "rerun from the chosen project_root" (used by `dev where`/`dev
  status`/`dev` workflow commands/`project where`); a new
  "rerun_working_dir_set" kind adds "passing DIR relative to that
  project_root" and is used only by `working-dir set`. `tests/cli_test.py`
  test (j) asserts each command gets the wording that fits it.
- `config_model.md` and a new "Closeout notes" section in the resolved WI
  state that criterion 6's "submodules and nested clones keep their current
  behaviour" describes plain projects; inside a symlinked external tree they
  now use the working_dir.
- `project/focus/current_focus.md` and `project/roadmap/roadmap.md` now
  describe both WIs as resolved (roadmap Phase 9 done) with no active work
  item.

# Validation

- `./scripts/format --check --diff`: pass
- `./scripts/lint`: pass
- `./scripts/test`: 404 tests OK
- `lrh validate`: 0 errors, 0 warnings

# Follow-up

- Still optional (from the PR #119 closeout note, not in this scope): from a
  submodule of a linked worktree, `dev` uses the working_dir rather than the
  enclosing worktree.
