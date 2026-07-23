---
execution_id: 2026_07_22_21_51_53_TAURWORKS_PACKAGING_DESIGN_66BBE8_CONFIRM
prompt_id: PROMPT(AD_HOC:TAURWORKS_PACKAGING_DESIGN_66BBE8_CONFIRM)[2026-07-22T21:50:22-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/taurworks/pull/77
commit:
created_at: 2026-07-22T21:51:53-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/77
session_transcript: pending
---

# Summary

Pre-merge confirm-fixes pass on PR #77, verifying the prior
`/lrh-review-response` round (`PROMPT(AD_HOC:TAURWORKS_PACKAGING_DESIGN_66BBE8_REVIEW)`)
against the live `HEAD` diff, independent of that pass's own claims.

# Result

Fetched all threads via `lrh github threads --mode raw --state all` filtered
to `isResolved == false`: **9 unresolved threads**, one more than the 8
comments the prior `/lrh-review-response` pass reported fixing — comment
`r3628356503` ("Honor XDG_CONFIG_HOME in setup's default path", codex) was
present in the original comment fetch but was missed in that pass's summary
and fix.

Classified each thread against the current diff (`gh pr diff 77`):

- **Clear-satisfied (8), resolved via `resolveReviewThread`:**
  - `r3628356091` (copilot) — "confirmed by reading repo" overstatement re:
    `tl.source` — verified softened in Purpose §1.
  - `r3628356118` (copilot) — `bin/` "30 files" vs actual 27 — verified
    corrected.
  - `r3628356151` (copilot) — `scripts/install` implied to exist — verified
    reworded to future/proposed tense.
  - `r3628356174` (copilot) — `sourceme/` "stays packaged" vs. `setup.py`
    reality — verified caveat added.
  - `r3628356192` (copilot) — `TAURWORKS_SHELL_HELPER_PATH` mischaracterized
    as flag+env pattern — verified corrected.
  - `r3628356488` (codex) — PATH-loss guard misses post-`conda activate`
    calls — verified new paragraph added covering internal call sites.
  - `r3628356495` (codex) — `migrate_legacy_projects.py` wrongly swept into
    `bin/` split — verified exemption added to Decisions #2 and the
    corresponding Options-considered/open-questions sections.
  - `r3628356500` (codex) — install shim should be non-editable `pipx
    install` — verified corrected.
- **Unaddressed (1), left unresolved:**
  - `r3628356503` (codex) — `XDG_CONFIG_HOME` handling — confirmed absent
    from the doc (`grep -n "XDG_CONFIG_HOME" project/design/packaging_and_install.md`
    returns nothing). User directed running `/lrh-review-response` next to
    address it.

Thread-resolution verdict (Step 6): **not green** — 1 thread (`r3628356503`)
remains open, by design, pending the follow-up `/lrh-review-response` run.

# Validation

- CI: `gh pr checks 77 --required` returned "no required checks reported";
  confirmed via `gh api repos/xenotaur/taurworks/branches/master/protection`
  (404 "Branch not protected") that no required-check rule is configured on
  `master` — not a reporting-delay false negative. Fell back to the
  unfiltered aggregate: `gh pr checks 77 --json name,state,bucket` — 4/4
  `lint-and-test` jobs SUCCESS.
- No source or design-doc changes made in this pass (verification only);
  no lint/format/test re-run needed beyond the CI state above.

# Follow-up

- `/lrh-review-response` to be run next for `r3628356503` (XDG_CONFIG_HOME
  handling in `taurworks setup`'s default path).
- `session_transcript: pending` should be updated to
  `claude-app:<session-id>` after this session ends.
- Final merge readiness (thread-resolution AND CI, re-checked against the
  post-push `HEAD`) is deferred until after the follow-up
  `/lrh-review-response` run resolves the remaining thread.
