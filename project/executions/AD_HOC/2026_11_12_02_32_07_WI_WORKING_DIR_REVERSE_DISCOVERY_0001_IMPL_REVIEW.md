---
execution_id: 2026_11_12_02_32_07_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_WORKING_DIR_REVERSE_DISCOVERY_0001_IMPL_REVIEW)[2026-11-12T02:30:15+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_11_11_05_46_07_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_IMPL_REVIEW
pr: https://github.com/xenotaur/taurworks/pull/119
commit:
created_at: 2026-11-12T02:32:07+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/119
session_transcript: pending
---

# Summary

Round 2 of review-response for PR #119, run inline from `/lrh-land`. It
addresses the substitute PR-mode review of `a0a5127`, whose findings
tripped the stop-work condition. The user chose "Fix in PR". Fixes are in
commit `fcca908`.

# Result

1. **Regression:** `dev test` run from a `git worktree` inside the external
   working_dir target ran the main checkout's `scripts/test`. On master it
   ran the worktree's, because the project wasn't found and the nearest git
   root won. I reproduced this directly by comparing a HEAD and an
   `origin/master` checkout.
   - Fix: `dev.gather_dev_where_diagnostics` now prefers a git work tree
     nested strictly inside the resolved working_dir (`_is_nested_work_tree`)
     over the working_dir itself.
   - Tier 1 `[dev.commands]` still come from `project_root`.
   - This also applies to worktrees physically inside a project.
   - Test: `test_dev_test_in_nested_worktree_runs_the_worktree_script`.
2. **Minor:** a non-UTF-8 global `config.toml` crashed `dev where` outside
   any project, because the registry and workspace reads didn't catch
   `UnicodeDecodeError`.
   - Fix: both global-config readers in `manager.py` catch it, and
     `find_project_root_for_path` treats an `OSError` from
     `gather_global_projects` (an unreadable workspace) as "no match".
   - Test: `test_non_utf8_global_config_does_not_crash_dev_where`.
- **Not changed:** finding 3 (the broad-`$HOME` `working_dir` caveat) and
  finding 4 (the wording aside in the "rerun" guidance) are non-blocking
  and recorded as follow-ups.
- README and `config_model.md` describe the worktree precedence.

# Validation

- `./scripts/format --check --diff`: pass
- `./scripts/lint`: pass
- `./scripts/test`: 396 tests OK
- `lrh validate`: 0 errors, 0 warnings

# Follow-up

- Confirm-fixes round 2, with a fresh substitute review: these were
  non-thread findings.
- Docs caveat for a broad `working_dir` target, and tidier "rerun" wording.
