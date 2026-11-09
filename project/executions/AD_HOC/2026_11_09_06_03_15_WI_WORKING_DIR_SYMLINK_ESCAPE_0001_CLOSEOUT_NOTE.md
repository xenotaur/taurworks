---
execution_id: 2026_11_09_06_03_15_WI_WORKING_DIR_SYMLINK_ESCAPE_0001_CLOSEOUT_NOTE
prompt_id: PROMPT(AD_HOC:WI_WORKING_DIR_SYMLINK_ESCAPE_0001_CLOSEOUT_NOTE)[2026-11-09T06:03:07+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_11_09_05_36_39_WI_WORKING_DIR_SYMLINK_ESCAPE_0001
pr: https://github.com/xenotaur/taurworks/pull/117
commit: 6cb00f2ff66fa1cdde3d1efd2a54220d056ee6ad
created_at: 2026-11-09T06:03:15+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/117
session_transcript: claude-app:1b69806b-4260-4637-95d0-46434a8c5576
---

# Summary

Closeout note for PR #117 (WI-WORKING-DIR-SYMLINK-ESCAPE-0001), landed via
`/lrh-execute` → `/lrh-implement` → `/lrh-land` and squash-merged as
`6cb00f2`. The primary record
(`2026_11_09_05_36_39_WI_WORKING_DIR_SYMLINK_ESCAPE_0001`) can't be edited,
so this record carries the CHAIN-NOTE.

# Result

CHAIN-NOTE: cycles=1; stops=0; gates=[chain, plan-divergence, land, confirm, merge]; friction=none; self_review_rounds=1; bot_rounds=2; note="Copilot and Codex auto-reviewed first push 4b6074d clean; no review threads; substitute PR-mode self-review on _CONFIRM head 1191796 clean (README precision nit accepted); plan-divergence gate fired once (shell_helper_test.py + README added, approved); Open Question (working-dir set DIR mapping) decided at chain gate; PR-mode _SELFREVIEW record committed at closeout to avoid moving the PR head."

# Validation

- PR state verified `MERGED` (merge commit `6cb00f2`) before any closeout
  edits.
- `lrh validate` run after closeout edits.

# Follow-up

- `taurworks dev ...` commands don't find the project after `tw activate`
  into an external work tree, because discovery uses the physical cwd.
  Needs its own work item.
- `project/focus/current_focus.md` and `project/roadmap/roadmap.md` still
  describe this WI as proposed. They need a focus/roadmap refresh.
