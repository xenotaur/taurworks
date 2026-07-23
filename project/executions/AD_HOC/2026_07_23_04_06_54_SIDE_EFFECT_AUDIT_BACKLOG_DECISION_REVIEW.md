---
execution_id: 2026_07_23_04_06_54_SIDE_EFFECT_AUDIT_BACKLOG_DECISION_REVIEW
prompt_id: PROMPT(AD_HOC:SIDE_EFFECT_AUDIT_BACKLOG_DECISION_REVIEW)[2026-07-23T03:39:36-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/taurworks/pull/81
commit: 76d9e1cd341fa564e71dcefbfe971fd670aa6eb9
created_at: 2026-07-23T04:06:54-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/81
session_transcript: claude-app:146d1a52-87d7-4028-97f7-b7118179f5d8
---

# Summary

Address 5 review comments on PR #81 (`chore/side-effect-audit-backlog-decision`),
a doc-only PR recording a design decision, a new `project/design/backlog.md`,
and corrections to `project/audits/side_effects.md`.

# Result

- copilot-pull-request-reviewer: `backlog.md`'s "eval/export calls in
  taurworks-shell.sh" claim was imprecise — verified via `grep` that the
  file has no literal `export` statements, only `eval` (including one that
  evaluates generated export commands). Reworded accordingly.
- copilot-pull-request-reviewer: `backlog.md`'s
  `project/audits/side_effects.md:449` citation was brittle — verified the
  line had already drifted to 466 after an earlier edit in this same PR,
  before the reviewer even commented. Replaced with a stable section-name
  reference.
- copilot-pull-request-reviewer: fixed a grammar error in `backlog.md`
  ("expects to occasionally ... going forward" was missing a verb/object).
- copilot-pull-request-reviewer + chatgpt-codex-connector (P2, same
  underlying issue): my earlier fix to recommendation #1's status text
  corrected one stale `.taurworks/project-setup.source` claim but left 4
  other mentions elsewhere in the same audit doc contradicting it
  (Executive findings #1; the legacy `taurworks create NAME` inventory
  entry; "Scripts and shell commands" Q3; "Filesystem and config mutation"
  Q2 — exact locations chatgpt-codex-connector cited: lines 62-66, 441-444,
  593-594, 614-618). Verified via `git log -p -S` that all were superseded
  by `WI-ACTIVATION-PRODUCERS-0001` (commit `7d8e777`, 2026-07-15), which
  post-dates this audit's 2026-05-17 writing. Fixed all 4, plus 2 more
  instances of the identical staleness the reviewers didn't explicitly cite
  (the "legacy top-level `taurworks activate NAME`" and "Conda activation"
  inventory entries) — fixing only the named lines would have left the same
  underlying contradiction elsewhere in the document.

All 5 comments fixed; none skipped.

# Validation

- `scripts/format --check --diff` — clean, 28 files unchanged
- `scripts/lint` (black + ruff) — clean
- `lrh validate` — 0 new errors (4 pre-existing `contributors.md` errors,
  unrelated to this PR)

# Follow-up

- `session_transcript: pending` — update to `claude-app:<session-id>` after
  this session ends.
- Suggest running `/lrh-confirm-fixes` on PR #81 before merge to verify the
  fixes against the current diff and resolve the review threads.
