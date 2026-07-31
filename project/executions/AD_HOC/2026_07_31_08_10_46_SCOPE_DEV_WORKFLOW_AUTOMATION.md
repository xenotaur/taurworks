---
execution_id: 2026_07_31_08_10_46_SCOPE_DEV_WORKFLOW_AUTOMATION
prompt_id: PROMPT(AD_HOC:SCOPE_DEV_WORKFLOW_AUTOMATION)[2026-07-31T08:10:46+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/taurworks/pull/98
commit: 18d00730c4b0729aab91140977fffe2b2aea4b48
created_at: 2026-07-31T08:10:46+00:00
agent: claude_app
instruction_source: conversational session — user asked to decide taurworks dev ...'s workflow-automation scope; I surveyed existing design docs (design.md, unified_command_model.md) and this repo's own scripts/ layout, found a real inconsistency between design.md's and roadmap.md's "higher-risk commands" lists, proposed a narrow delegate-only v1, and the user confirmed
session_transcript: claude-app:43689ae3-1b8e-45ff-b3b8-75e8997239fb
---

# Summary

Decide and record the scope of `taurworks dev ...` workflow automation
beyond its current read-only `dev where`/`dev status` diagnostics —
`project/roadmap/roadmap.md` and `project/focus/current_focus.md` had both
left this as an explicitly open, undecided question since Phase 4.

# Result

**Survey**: `project/design/design.md` and
`project/design/unified_command_model.md` already specify a full
15-command `dev` namespace and a 3-tier resolution model (explicit config
→ project-local script → built-in per-project-type default), but no dev
workflow command beyond diagnostics was ever implemented. This repo's own
`scripts/` directory already has 7 of the 15 specified commands (`clean`,
`develop`, `test`, `smoke`, `lint`, `format`, `build`), making delegation
to most of them immediately dogfoodable.

**Inconsistency found and fixed**: `design.md`'s "higher-risk commands"
list (`clean`, precommit, publish, update, sandbox) and `roadmap.md`'s
Phase 6 deferred list (sandbox, precommit, publish, version, validate,
update) disagreed — `clean` was flagged risky in one but not the other,
and `version`/`validate` vice versa. Reconciled both to the same v1/
deferred split.

**Second real gap, caught by review**: the first version of this decision
included `develop` in the "reversible, low-risk" v1 set. Review pointed
out that `scripts/develop` in this repo actually runs `pip install`
(constrained developer-mode setup), which is dependency-mutating —
directly contradicting Phase 6's own principle of deferring
dependency-mutating operations until guardrails are proven. Moved
`develop` into the deferred set across all four docs.

**Decision (final)**: v1 is delegate-only (Tier 1 config override + Tier
2 project-local-script), covering 6 commands with existing, non-mutating
scripts in this repo (`clean`, `test`, `smoke`, `lint`, `format`,
`build`). Deferred: `init`, `develop`, `coverage`, `update`, `precommit`,
`publish`, `sandbox`, `version`, `validate` (higher-risk: irreversible,
packaging/release, dependency-mutating, or not-yet-semantically-defined),
and Tier 3 (built-in per-project-type defaults, no concrete design yet).

**Docs updated**: `project/roadmap/roadmap.md` (Phase 6 rewritten with
the decided v1/deferred split, "Current phase snapshot"/"In scope now"
updated), `project/focus/current_focus.md` (title/frontmatter, Current
Focus prose, Active direction/In-scope/Out-of-scope lists),
`project/design/design.md` ("Transparency and safety"'s higher-risk list
reconciled and `develop` corrected; the "Implementation sequence status"
section's stale claims that legacy inspect/migrate and trusted hooks
"remain design-only" were also caught by review and fixed, since both are
implemented; the "safety boundary" text block below it had the same
staleness and was fixed too), `project/design/unified_command_model.md`
("Status note" and "Remaining implementation sequence" corrected
similarly — items 1/2/4 of its old sequence were already resolved
elsewhere and had gone stale, and `develop` moved to the deferred list).

Also removed two stray untracked files
(`project/work_items/proposed/WI-TAURWORKS-SETUP-0001.md`,
`project/work_items/proposed/WI-TW-PATH-LOSS-DIAGNOSTIC-0001.md`) found
on disk during this session: leftover pre-implementation duplicates from
an earlier `git reset --hard HEAD` fixup this session, superseded by the
real resolved versions of the same files, never committed.

Drafted the implementation work item,
`WI-DEV-WORKFLOW-AUTOMATION-0001`, as a separate follow-up (its own PR,
after this one lands), per the packaging-series precedent of landing a
design/scope decision before drafting the work item(s) that implement it.

CHAIN-NOTE: cycles=2; stops=1; gates=[merge]; friction="review caught a real scoping mistake in the original decision (develop wrongly classified low-risk despite scripts/develop running pip install), and a cold confirm-fixes subagent caught that my own first-round fix for it was incomplete (a straggler v1 mention survived in roadmap.md's summary paragraph, requiring a second confirm-fixes round to close)"; note="PR #98 merged 18d0073; taurworks dev workflow-automation v1 scope decided as clean/test/smoke/lint/format/build (develop moved to deferred), design.md/roadmap.md's disagreeing higher-risk-command lists reconciled; WI-DEV-WORKFLOW-AUTOMATION-0001 drafted and approved, to be opened as its own PR next"

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- No Python source changed; `scripts/format`/`scripts/lint`/`scripts/test`
  not applicable.

# Follow-up

- PR #98 merged (`18d0073`); review response and confirm-fixes already
  landed against it before merge. Next: draft `WI-DEV-WORKFLOW-AUTOMATION-0001`
  in a fresh branch off the updated master.
