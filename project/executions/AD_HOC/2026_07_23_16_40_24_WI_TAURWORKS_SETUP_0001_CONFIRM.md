---
execution_id: 2026_07_23_16_40_24_WI_TAURWORKS_SETUP_0001_CONFIRM
prompt_id: PROMPT(AD_HOC:WI_TAURWORKS_SETUP_0001_CONFIRM)[2026-07-23T16:40:05-04:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/taurworks/pull/84
commit: bcb45cd9c9d82f27e861bbebe8e77f2703a56efc
created_at: 2026-07-23T16:40:24-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/84
session_transcript: claude-app:43689ae3-1b8e-45ff-b3b8-75e8997239fb
---

# Summary

Pre-merge confirm-fixes pass on PR #84, verifying the
`/lrh-review-response` round
(`PROMPT(AD_HOC:WI_TAURWORKS_SETUP_0001_REVIEW)[2026-07-23T16:08:09-04:00]`)
against the live `HEAD` diff, independent of that pass's own claims. Since
this session authored the fixes being verified, the classification was
dispatched to a cold subagent (PR URL, diff, and comment bodies only, no
session memory) per the user's confirmed opt-in.

# Result

Fetched all threads via `lrh github threads --mode raw --state all`
filtered to `isResolved == false`: 3 unresolved threads (same 3 addressed
in the prior `/lrh-review-response` round). Subagent classification
against the current diff (`gh pr diff 84`):

- **Clear-satisfied, resolved via `resolveReviewThread`:**
  - `r3640731603` (chatgpt-codex-connector, P1, "Keep setup and refresh on
    the same helper path") — Required Change #3 + acceptance + integration
    test all now specify matching `TAURWORKS_SHELL_HELPER_PATH →
    XDG_CONFIG_HOME → ~/.config` resolution in `tw shell refresh`.
  - `r3640731613` (chatgpt-codex-connector, P2, "Resolve the checkout root
    before installing") — Required Change #7 now specifies deriving
    `repo_root` matching `scripts/build`/`scripts/check-workflows`'s
    pattern before running `pipx install`.
- **Partial, left unresolved:**
  - `r3640731609` (chatgpt-codex-connector, P1, "Include the tl source
    file in the installed package") — the subagent found the fix
    incomplete: Required Change #4 only says packaging "depends on
    `WI-BIN-REPO-SPLIT-0001`... (or as a prerequisite step here)" —
    conditional, not a commitment — and `artifacts_expected` still omits
    `setup.py`/`sourceme/`. The reviewer's core ask ("neither the required
    changes nor artifacts_expected calls for changing the package data")
    is only conditionally met. This overrides my own earlier inline
    Clear-satisfied classification from the review-response pass; the
    subagent's independent read is more rigorous and is what's recorded
    here.

Subagent also independently verified the `depends_on: []` sanity check:
confirmed `WI-BIN-REPO-SPLIT-0001.md` does not exist in
`project/work_items/proposed/` or `resolved/` on this branch, so the
review-response pass's decision to revert a formal `depends_on` reference
(to avoid `UNKNOWN_DEPENDENCY`) was correct.

Thread-resolution verdict (Step 6): **not green** — 1 thread
(`r3640731609`) remains open, by design, pending a follow-up
`/lrh-review-response` round to make the `package_data` fix unconditional.

# Validation

- CI: `gh pr checks 84 --required` returned "no required checks reported";
  confirmed via `gh api repos/xenotaur/taurworks/branches/master/protection`
  (404 "Branch not protected") that no required-check rule is configured —
  not a reporting-delay false negative. Unfiltered aggregate: `gh pr checks
  84 --json name,state,bucket` — 4/4 `lint-and-test` jobs SUCCESS.
- No source or work-item changes made in this pass (verification/resolution
  only).

# Follow-up

- `/lrh-review-response` to be run next for `r3640731609`: commit the WI to
  adding the `sourceme/` `package_data` entry directly (regardless of
  `WI-BIN-REPO-SPLIT-0001`'s merge order) and add `setup.py`/`sourceme/` to
  `artifacts_expected`.
- `session_transcript: pending` should be updated to
  `claude-app:<session-id>` after this session ends.
- Final merge readiness (thread-resolution AND CI, re-checked against the
  post-push `HEAD`) is deferred until the follow-up `/lrh-review-response`
  run resolves the remaining thread.
