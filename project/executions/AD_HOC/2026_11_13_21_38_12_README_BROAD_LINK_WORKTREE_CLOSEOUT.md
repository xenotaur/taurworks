---
execution_id: 2026_11_13_21_38_12_README_BROAD_LINK_WORKTREE_CLOSEOUT
prompt_id: PROMPT(AD_HOC:README_BROAD_LINK_WORKTREE_CLOSEOUT)[2026-11-13T21:38:12+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/taurworks/pull/121
commit: 65f328acd62d39d069e09e7cff9bd0d35679179e
created_at: 2026-11-13T21:38:12+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/121
session_transcript: claude-app:bb8a0d8f-eb4a-4db9-9288-bdad683c73f2
---

# Summary

Backfill execution record for PR #121 (README: note the linked-worktree
exception for broad working_dir links), landed via `/lrh-land`. The PR
skipped a primary execution record as a small obvious fix (PROMPTS.md), so
this record carries the work's traceability and the chain note.

The change adds the linked-worktree exception to README.md's broad
working_dir caveat: a linked `git worktree` nested in the link's target runs
`dev` commands in the worktree, any other checkout runs in the link's
target. It follows up PR #120's self-review nit.

# Result

- Merged as `65f328acd62d39d069e09e7cff9bd0d35679179e` (squash).
- Side records landed with it:
  `2026_11_13_20_14_19_README_BROAD_LINK_WORKTREE_CONFIRM` and
  `2026_11_13_20_17_52_README_BROAD_LINK_WORKTREE_SELFREVIEW`.
- No work item or workstream to resolve.
- CHAIN-NOTE: cycles=1; stops=0; gates=[chain, confirm, merge]; friction=none; self_review_rounds=1; bot_rounds=1; note="backfill path; README-only follow-up to PR #120"

# Validation

- CI on the merged head `6f0c76e`: 4/4 `lint-and-test` SUCCESS.
- Copilot and Codex reviewed `0e062bd` with no findings; a cold-context
  PR-mode self-review of `6f0c76e` found nothing blocking.
- `lrh validate` run before committing this record.

# Follow-up

- None.
