---
execution_id: 2026_07_31_04_30_23_WI_LEGACY_MIGRATE_TL_FALLBACK_0001_ABANDON
prompt_id: PROMPT(WI-LEGACY-MIGRATE-TL-FALLBACK-0001:WI_LEGACY_MIGRATE_TL_FALLBACK_0001_ABANDON)[2026-07-31T04:30:23+00:00]
work_item: WI-LEGACY-MIGRATE-TL-FALLBACK-0001
status: in_progress
rerun_of:
pr: pending
commit: pending
created_at: 2026-07-31T04:30:23+00:00
agent: claude_app
instruction_source: conversational session — user asked to decide WI-LEGACY-MIGRATE-TL-FALLBACK-0001's fate; I audited the real workspace, found zero remaining Admin/project-setup.source files, recommended abandoning the WI, and the user confirmed
session_transcript: claude-app:43689ae3-1b8e-45ff-b3b8-75e8997239fb
---

# Summary

Resolve the deferred question `project/roadmap/roadmap.md`/
`project/focus/current_focus.md` were both holding open since 2026-07-25:
does `WI-LEGACY-MIGRATE-TL-FALLBACK-0001` still have a target? Direct
audit of the real `~/Workspace` found none. Marked the WI `status:
abandoned` (LRH's supported terminal non-implementation status,
`STATUS_BUCKETS = (proposed, active, resolved, abandoned)`), moved it to
`project/work_items/abandoned/` (new bucket directory in this repo), and
updated the roadmap/focus docs accordingly.

# Result

**Audit finding**: `find ~/Workspace -path "*/Admin/project-setup.source"`
returned zero matches. Every one of the 11 projects named in the WI's
Problem/Context (`LCATS`, `EmbodiedAI`, `CentaursGuide`, `ImageWorks`,
`LogicalRoboticsHarness`, `Narramorph`, `Novarc`, `ProsocialRobotics`,
`PythonGames`, `Taxman`, `Taurcode`) has already had its
`Admin/project-setup.source` retired by hand: most renamed to
`Admin/project-setup.source~` (backup) with the active copy now at
`.taurworks/project-setup.source`, two (`Taurcode`, `LCATS`) renamed
`.legacy`, and `ImageWorks`/`Scansion`'s `Admin/` directories now
completely empty. This directly answers the roadmap's own held condition
("pending confirmation ... that legacy projects still exist needing it")
as: no.

**Disposition**: `project/work_items/proposed/WI-LEGACY-MIGRATE-TL-FALLBACK-0001.md`
moved to `project/work_items/abandoned/` (new bucket; `lrh work-items
organize --check` confirms correct placement, `lrh validate` confirms
`abandoned` is an accepted `status:` value). `resolution:` records the
audit finding plus the WI's own pre-existing Risk Notes (the `legacy
migrate` matcher's variable-indirection gap, out of scope, means the
completeness check would rarely pass for real scripts even if any had
remained unretired) as the combined rationale.

**Docs updated**: `project/roadmap/roadmap.md` (Current phase snapshot
date and narrative, dropped the now-moot "confirm/implement" bullets from
In/Out of scope) and `project/focus/current_focus.md` (title, `updated`/
`basis` frontmatter, Current Focus prose, Active direction/In-scope/
Out-of-scope lists) to state the item is abandoned rather than deferred.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items organize --check`: 17 inspected, 0 changes needed (1
  skip: `project/work_items/README.md`, expected, no WI-* id).
- No Python source changed; `scripts/format`/`scripts/lint`/`scripts/test`
  not applicable.

# Follow-up

- Next: open PR, wait for reviewer comments, run
  `/lrh-review-response`/`/lrh-confirm-fixes`, then `/lrh-closeout` after
  merge.
