---
execution_id: 2026_11_13_02_59_53_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_WORKING_DIR_REVERSE_DISCOVERY_0001_SELFREVIEW)[2026-11-13T02:59:53+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_11_11_03_45_54_WI_WORKING_DIR_REVERSE_DISCOVERY_0001
pr: https://github.com/xenotaur/taurworks/pull/119
commit: 9be45caa6efe6a5f8067a1550cb0036db6113bc3
created_at: 2026-11-13T02:59:53+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/119
session_transcript: claude-app:1b69806b-4260-4637-95d0-46434a8c5576
---

# Summary

PR-mode `/lrh-self-review` substitute pass on PR #119 at `e531057` (the
round-4 `_CONFIRM` head, which was merged). Cold-context subagent,
report-only. This record was created at closeout, on `master`, rather than pushed to the PR, so the PR head wasn't moved (the PR #117/#118 precedent).

# Result

- Verdict: safe to merge as-is; no blocking defects.
- The `commondir` check was verified with real git across absolute and
  relative worktrees, `--relative-paths` worktrees, a worktree of a
  submodule, plain and `worktrees/`-named submodules, pruned admin dirs and
  malformed files.
- 72 command/cwd pairs matched master apart from the new `resolved_by`
  line and reworded text.
- Non-blocking wording gap: inside a symlinked external tree, submodules
  and nested clones now use the working_dir, as Required Change 5 intends.
  But criterion 6's parenthetical ("keep their current behaviour") is only
  literally true for plain projects. The user merged knowing this, and it
  is noted in the WI resolution.
- Polish (not changed): from a submodule *of* a linked worktree, `dev`
  uses the working_dir (the nearest-git-root rule, same as master).

# Validation

404 tests; format, lint and `lrh validate` clean; real-git experiments.

# Follow-up

- Optional: reword criterion 6's parenthetical in a future docs pass.
