---
execution_id: 2026_07_18_17_06_08_WI_TL_BREAKGLASS_0001_REVIEW
prompt_id: PROMPT(AD_HOC:WI_TL_BREAKGLASS_0001_REVIEW)[2026-07-18T16:54:22-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/taurworks/pull/72
commit: df31ad7
created_at: 2026-07-18T17:06:08-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/72
session_transcript: pending
---

# Summary

Address three open review comments on PR #72 (WI-TL-BREAKGLASS-0001 planning
document): a nested-backtick markdown bug, an incomplete stale-shell-helper
mitigation, and an underspecified conditional in Required Changes item 4.

# Result

All three comments verified valid by direct inspection of
`WI-TL-BREAKGLASS-0001.md` before fixing; all fixed (commit df31ad7):

1. **Nested-backtick markdown bug** — Required Changes item 2 wrapped a
   heading containing its own backtick-quoted `tl` in an outer backtick
   span (`` `## Interim `tl` helper ...` ``), breaking rendering. Changed
   the outer wrapper to quotes so the inner `` `tl` `` code span renders
   correctly.
2. **Incomplete stale-shell-helper mitigation** — the item 2 parenthetical
   said only "re-source `~/.config/taurworks/taurworks-shell.sh` after every
   taurworks update," omitting the regenerate step. Re-sourcing an
   unregenerated file is exactly the bug this session found live during
   dogfooding (see [[project-dogfood-recovery-plan]]). Reworded to state
   both steps: regenerate via `taurworks shell print > ...` and then
   re-source.
3. **Item 4's conditional shape was underspecified** — "make it conditional"
   implied a Python-side-only fix, but the true sourcing outcome depends on
   shell-only state (`--legacy`/`--no-legacy` flags, TTY availability, the
   interactive prompt's answer) that `project_resolution.py`'s diagnostics
   function never receives. Traced the real decision logic in
   `taurworks-shell.sh`'s `_tw_activate` (~lines 305-323) to confirm a
   Tier-1/trust-only condition would be wrong in real cases. Reworded the
   requirement to require either (a) threading the actual sourcing outcome
   from the shell layer into the diagnostics (mirroring how
   `TAURWORKS_ACTIVATION_PROJECT_ROOT` was threaded through in PR #70), or
   (b) rewording the guidance to be accurate regardless of outcome.

Nothing was skipped.

# Validation

- `lrh validate` — no new errors (4 known pre-existing `contributors.md`
  errors remain)
- This PR only modifies a planning document (`WI-TL-BREAKGLASS-0001.md`);
  no code changed, so `scripts/format`/`scripts/lint`/`scripts/test` are not
  applicable to this commit.

# Follow-up

- On merge: closeout via `/lrh-closeout` (mark this record landed, resolve
  or advance `WI-TL-BREAKGLASS-0001` per user direction).
- Resolving the three GitHub review conversations is a human action.
- The requirement changes made here (items 2 and 4) are guidance for the
  eventual `/lrh-implement WI-TL-BREAKGLASS-0001` pass, not yet executed.
