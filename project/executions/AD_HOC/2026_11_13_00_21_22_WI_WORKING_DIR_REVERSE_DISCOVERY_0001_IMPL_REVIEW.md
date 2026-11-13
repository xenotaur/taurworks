---
execution_id: 2026_11_13_00_21_22_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_WORKING_DIR_REVERSE_DISCOVERY_0001_IMPL_REVIEW)[2026-11-13T00:19:44+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_11_13_00_00_17_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_IMPL_REVIEW
pr: https://github.com/xenotaur/taurworks/pull/119
commit: 9be45caa6efe6a5f8067a1550cb0036db6113bc3
created_at: 2026-11-13T00:21:22+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/119
session_transcript: claude-app:1b69806b-4260-4637-95d0-46434a8c5576
---

# Summary

Round 4 of review-response for PR #119, run inline from `/lrh-land`. It
addresses the substitute PR-mode review of `2d7f54b`. That review judged
the PR safe to merge except for one low-severity edge case that contradicts
amended criterion 7. The user chose "Fix it, then merge". Fixes are in
commit `2faff16`.

# Result

- **Finding:** a submodule added at `worktrees/<name>` has
  `gitdir: …/.git/modules/worktrees/<name>`, whose next-to-last part is
  `worktrees`, so `_is_linked_worktree` mistook it for a linked worktree.
  The reviewer reproduced it with real git; I re-verified it by reasoning
  from the code, then confirmed the fix with real git
  (`git submodule add … worktrees/trap`).
- **Fix:** `_is_linked_worktree` resolves the `gitdir` path against the
  checkout and also requires a `commondir` file there. Git writes one for
  every linked worktree's admin dir and never for a submodule's git dir.
  No `git` process is run.
- **Tests:**
  - `dev_test.LinkedWorktreeDetectionTest` was rebuilt around real admin
    dirs: with and without `commondir`, a plain submodule, the
    `worktrees/trap` submodule, a `.git` directory, and empty or malformed
    files.
  - `cli_test.test_dev_linked_worktree_rule_in_plain_project` adds the trap
    submodule and the main-checkout case (both use the working_dir).
- **Polish from the same review:**
  - README and `config_model.md` now say the checkout considered is the
    one containing the cwd (its nearest git root).
  - WI criterion 7, Required Change 5 and test (p) mention `commondir`.
- **Left as-is (matches master and the WI):** a worktree beside, rather
  than inside, the working_dir is not preferred.
- **Real-git dogfood:** the worktree under the external tree is still
  preferred; the `worktrees/trap` submodule uses the working_dir.

# Validation

- `./scripts/format --check --diff`: pass
- `./scripts/lint`: pass
- `./scripts/test`: 404 tests OK
- `lrh validate`: 0 errors, 0 warnings

# Follow-up

- Confirm-fixes round 4 with a fresh substitute review.
