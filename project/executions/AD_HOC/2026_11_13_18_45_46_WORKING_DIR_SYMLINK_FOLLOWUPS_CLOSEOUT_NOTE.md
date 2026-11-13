---
execution_id: 2026_11_13_18_45_46_WORKING_DIR_SYMLINK_FOLLOWUPS_CLOSEOUT_NOTE
prompt_id: PROMPT(AD_HOC:WORKING_DIR_SYMLINK_FOLLOWUPS_CLOSEOUT_NOTE)[2026-11-13T18:45:34+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_11_13_03_07_45_WORKING_DIR_SYMLINK_FOLLOWUPS
pr: https://github.com/xenotaur/taurworks/pull/120
commit: 1886d34b37f22c8c132b55a5d6266076004c7831
created_at: 2026-11-13T18:45:46+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/120
session_transcript: claude-app:bb8a0d8f-eb4a-4db9-9288-bdad683c73f2
---

# Summary

Closeout note for PR #120 (follow-ups to WI-WORKING-DIR-SYMLINK-ESCAPE-0001
and WI-WORKING-DIR-REVERSE-DISCOVERY-0001), landed via `/lrh-land`. The
primary record (`2026_11_13_03_07_45_WORKING_DIR_SYMLINK_FOLLOWUPS`) body is
immutable, so this record carries the CHAIN-NOTE.

# Result

CHAIN-NOTE: cycles=1; stops=0; gates=[chain, confirm, merge]; friction=none; self_review_rounds=1; bot_rounds=1; note="Codex (5c71396) and Copilot (73d082f) reviewed clean on first push; no review threads. No automatic review landed on the _CONFIRM commit 4fcecd9, so a PR-mode substitute self-review ran: clean, 4 non-blocking nits (README broad-link sentence omits the linked-worktree exception; left for a follow-up). SHA-locked squash merge succeeded first try as 1886d34."

# Validation

- PR state verified `MERGED` (merge commit `1886d34`) before closeout edits.
- `lrh validate` run after closeout edits.

# Follow-up

- Optional: add the linked-`git worktree` exception to the README's
  broad-link sentence (`config_model.md` already states it).
- Still optional from the PR #119 closeout: from a submodule of a linked
  worktree, `dev` uses the working_dir rather than the enclosing worktree.
