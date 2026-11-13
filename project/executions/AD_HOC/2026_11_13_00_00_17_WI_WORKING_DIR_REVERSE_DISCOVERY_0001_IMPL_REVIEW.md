---
execution_id: 2026_11_13_00_00_17_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_WORKING_DIR_REVERSE_DISCOVERY_0001_IMPL_REVIEW)[2026-11-12T23:57:41+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_11_12_02_32_07_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_IMPL_REVIEW
pr: https://github.com/xenotaur/taurworks/pull/119
commit:
created_at: 2026-11-13T00:00:17+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/119
session_transcript: pending
---

# Summary

Round 3 of review-response for PR #119, run inline from `/lrh-land`. It
addresses the substitute PR-mode review of `4d15c27`. That review found a
blocking regression: round 2's nested-checkout preference in `dev` also
changed non-symlinked layouts (submodules, nested clones, and the Tier 1
cwd), against acceptance criterion 6. The user chose the "middle option"
after two rounds of explanation. Fixes are in commit `953b6e5`.

# Result

- **Verified:** round 2's `_is_nested_work_tree` applied regardless of how
  the project was found, so it changed plain-project behaviour.
- **Fix (`dev.py`):** `_is_nested_linked_worktree` prefers a nested checkout
  only when it is a linked `git worktree`. `_is_linked_worktree` reads the
  `.git` file and checks that the `gitdir:` path ends in `worktrees/<name>`,
  without running `git`. Submodules (`modules/<name>`), independent nested
  clones (a `.git` directory) and malformed files keep the working_dir.
- **WI amended in this PR, with the user's approval:**
  - Acceptance criterion 6 now carves out linked worktrees. Submodules and
    clones keep their current behaviour.
  - A new criterion specifies the `.git`-file test.
  - Required Change 5 describes the rule (later items renumbered).
  - Tests (n)–(p) added.
- **Tests:**
  - `cli_test.test_dev_linked_worktree_rule_in_plain_project`: worktree,
    submodule, independent clone and malformed `.git`, in a physically
    discovered project.
  - `dev_test.LinkedWorktreeDetectionTest`: parser cases.
  - The symlinked worktree fixture now uses a real `worktrees` gitdir.
- **Dogfood with real git** (`git worktree add`, `git submodule add`),
  inside a symlinked external tree:
  - main checkout → its own `scripts/test`
  - worktree → the worktree's own script
  - submodule → the working_dir's script, the same as in a plain project
- README and `config_model.md` narrowed to linked worktrees.

# Validation

- `./scripts/format --check --diff`: pass
- `./scripts/lint`: pass
- `./scripts/test`: 403 tests OK
- `lrh validate`: 0 errors, 0 warnings
- WI readiness: `prompt_ready: yes`

# Follow-up

- Confirm-fixes round 3 with a fresh substitute review.
- Still deferred: the broad-`$HOME` working_dir docs caveat, and the "rerun"
  wording aside.
