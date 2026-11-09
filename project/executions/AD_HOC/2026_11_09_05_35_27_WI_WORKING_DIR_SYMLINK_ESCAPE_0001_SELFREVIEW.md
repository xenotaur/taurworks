---
execution_id: 2026_11_09_05_35_27_WI_WORKING_DIR_SYMLINK_ESCAPE_0001_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_WORKING_DIR_SYMLINK_ESCAPE_0001_SELFREVIEW)[2026-11-09T05:35:22+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_11_09_05_36_39_WI_WORKING_DIR_SYMLINK_ESCAPE_0001
pr: https://github.com/xenotaur/taurworks/pull/117
commit: 6cb00f2ff66fa1cdde3d1efd2a54220d056ee6ad
created_at: 2026-11-09T05:35:27+00:00
agent: claude_app
instruction_source: "lrh-self-review diff-mode (lrh-implement Step 7.5) for project/work_items/proposed/WI-WORKING-DIR-SYMLINK-ESCAPE-0001.md"
session_transcript: claude-app:1b69806b-4260-4637-95d0-46434a8c5576
---

# Summary

Diff-mode `/lrh-self-review` pass (report-only, no `--apply`) on branch
`xenotaur/feat/wi-working-dir-symlink-escape-0001` before the PR's first
push, reviewing `git diff origin/master` (the repo's default branch is
`master`) against WI-WORKING-DIR-SYMLINK-ESCAPE-0001. A cold-context
general-purpose subagent did the review.

# Result

- Mode: diff, report-only. Verdict: the diff plausibly satisfies the WI. No
  blocking or correctness issues.
- Findings (2, both minor):
  1. Low: README.md lines 813 and 837 still said `working_dir` must
     "stay inside" or "resolve safely inside" `project_root`. The invoking
     session re-checked this directly and confirmed it. With the user's
     approval, the main session fixed it in commit 6badc88, outside this
     report-only pass.
  2. Very low: end-to-end coverage is asymmetric (`activate --print` is
     tested only with a dangling link, `dev where` only with a loop). The
     unit tests cover both cases for both helpers. No change was made.
- Design observation, out of scope: after `tw activate` `cd`s into an
  external work tree, `taurworks dev ...` commands use the physical cwd
  for discovery and don't find the project. The invoking session re-checked
  this directly: `dev where` from `Workspace/Dogfood/working_dir` reports
  `project_root: unresolved`. Recorded as a follow-up.
- No fixes were applied by this skill.

# Validation

The subagent ran `tests.project_internals_test`, `tests.cli_test` and
`tests.shell_helper_test` (196 tests, all OK on 3.11.8; internals also on
3.12 and 3.14), lint and format check, plus scratch edge-case scripts for
symlink detection.

# Follow-up

- Project discovery from inside a symlinked external work tree, so `dev`
  commands work after `tw activate`. Separate work item.
