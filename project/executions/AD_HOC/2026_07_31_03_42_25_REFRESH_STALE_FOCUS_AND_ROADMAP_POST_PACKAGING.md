---
execution_id: 2026_07_31_03_42_25_REFRESH_STALE_FOCUS_AND_ROADMAP_POST_PACKAGING
prompt_id: PROMPT(AD_HOC:REFRESH_STALE_FOCUS_AND_ROADMAP_POST_PACKAGING)[2026-07-31T03:42:25+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: pending
commit: pending
created_at: 2026-07-31T03:42:25+00:00
agent: claude_app
instruction_source: conversational session — user asked "what's left on the roadmap now", I identified project/roadmap/roadmap.md and project/focus/current_focus.md as stale (both still described the 3 just-resolved packaging WIs as proposed/prompt-ready), showed the proposed diff, and the user confirmed applying it
session_transcript: claude-app:43689ae3-1b8e-45ff-b3b8-75e8997239fb
---

# Summary

Refresh `project/roadmap/roadmap.md` and `project/focus/current_focus.md`
against the just-landed packaging/install series: all 4 work items drafted
from `project/design/packaging_and_install.md`
(`WI-BIN-REPO-SPLIT-0001`/PR #88, `WI-TAURWORKS-SETUP-0001`/PR #93,
`WI-TW-PATH-LOSS-DIAGNOSTIC-0001`/PR #94, `WI-TAURWORKS-DEBUG-FLAG-0001`/PR
#95) are now resolved, but both docs still described the latter three as
"proposed and prompt-ready" from before this session's work landed.
Follows the same pattern as the prior refresh, PR #90
(`2026_07_25_22_31_32_REFRESH_STALE_FOCUS_AND_ROADMAP_PR90`).

# Result

**`project/roadmap/roadmap.md`**: updated the "Current phase snapshot"
date and narrative to state all four packaging/install gaps are resolved
(previously said only the repo/package split was done, the other three
"proposed and prompt-ready"); reworded `WI-LEGACY-MIGRATE-TL-FALLBACK-0001`'s
framing from "pending confirmation after the packaging work above lands"
to "now that the packaging work above has landed"; updated "In scope now"
to drop "landing the three proposed work items" (done) in favor of
confirming whether `WI-LEGACY-MIGRATE-TL-FALLBACK-0001` is still needed;
marked "Phase 8 — Packaging and install cleanup" `(done)` (was "in
progress, tracked separately") and rewrote its bullet list to state all
four items resolved, with PR numbers.

**`project/focus/current_focus.md`**: same narrative update (title,
`updated`/`basis` frontmatter, "Current Focus" prose, "Active
direction"/"In scope now" lists); added the three newly-landed WIs
(`WI-TAURWORKS-SETUP-0001`, `WI-TW-PATH-LOSS-DIAGNOSTIC-0001`,
`WI-TAURWORKS-DEBUG-FLAG-0001`) to the "Already implemented (do not
re-plan)" list, which previously only had `WI-BIN-REPO-SPLIT-0001` from
this series.

Both files' `related_focus`/`related_roadmap` linkage on the 3 newly
resolved WIs was already correctly wired (`[FOCUS-CURRENT]`/
`[ROADMAP-INIT]`, set when they were drafted) — unlike PR #90's round,
there was no self-contradiction to fix this time since these WIs already
referenced the focus/roadmap IDs they're now marked resolved against.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- No Python source changed; `scripts/format`/`scripts/lint`/`scripts/test`
  not applicable.

# Follow-up

- `session_transcript: pending` should be updated to
  `claude-app:<session-id>` after this session ends.
- Next steps: open PR, wait for reviewer comments, run
  `/lrh-review-response`/`/lrh-confirm-fixes`, then `/lrh-closeout` after
  merge.
