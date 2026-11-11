---
execution_id: 2026_11_10_23_33_06_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_CONFIRM
prompt_id: PROMPT(AD_HOC:WI_WORKING_DIR_REVERSE_DISCOVERY_0001_CONFIRM)[2026-11-10T23:32:49+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_11_10_16_21_41_WI_WORKING_DIR_REVERSE_DISCOVERY_0001
pr: https://github.com/xenotaur/taurworks/pull/118
commit: e5114117b0f4204a47e002f0d99a46dc3cabef08
created_at: 2026-11-10T23:33:06+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/118
session_transcript: claude-app:1b69806b-4260-4637-95d0-46434a8c5576
---

# Summary

`/lrh-confirm-fixes` pass for PR #118, run inline from `/lrh-land`.
Verified against head `7e0a54f`, after review-response commit `90ea8e2`.

# Result

- Authoritative thread list: 3 threads, all from
  copilot-pull-request-reviewer (bot), all `isResolved == false` and
  `isOutdated == true`. `lrh request review_response`'s narrower filter hid
  them after the lines moved.
- Classified inline against `gh pr diff`. I authored the fixes in this
  session, so I offered a cold re-check; the user declined.
- All three were Clear-satisfied and resolved:
  1. `project working` can't reach the no-target branch. The WI now routes
     explicit existing-directory targets through the reverse lookup, drops
     `project working` from the no-target list, and adds test (i).
  2. The ambiguity guidance offered an unsupported action. It is now
     command-specific in the WI and `config_model.md`, with test (j).
  3. The `set` boundary was inconsistent. It is now one rule (the last
     symlink component) across the WI acceptance criteria, Required Change 4
     and `config_model.md`, and test (c) covers `working_dir/sub`.
- Surfaced exceptions: none. The user confirmed the batch live
  (`confirm_fixes_batch: always_confirm`).
- Step 6 thread verdict: green.
- Provisional CI at `7e0a54f`: 4 `lint-and-test` jobs pending. Step 8
  re-checks on the post-push head.

# Validation

- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Step 8: CI on the post-push head, then a REVIEW-LANDED check through a
  substitute PR-mode self-review. Copilot's `review_on_push` is false, and
  Codex reviews only when the PR opens.
