---
execution_id: 2026_11_14_00_14_13_DOC_WORK_END_USER_DOCS
prompt_id: PROMPT(AD_HOC:DOC_WORK_END_USER_DOCS)[2026-11-14T00:01:52+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/taurworks/pull/122
commit:
created_at: 2026-11-14T00:14:13+00:00
agent: claude_app
instruction_source: conversational session — user asked for comprehensive Diataxis end-user documentation of Taurworks (install, tw activate, tl fallback, full CLI) via /lrh-doc-work with scope widened beyond a single work reference
session_transcript: pending
---

# Summary

Broad end-user documentation pass run via `/lrh-doc-work`, with the skill's
scope deliberately widened at the user's request from "one merged work
reference, minimal edits" to "document the whole system for end users,
prioritizing usability, correctness, and comprehensiveness". The user
confirmed the layout (docs/ tree by Diataxis quadrant plus a slimmed README)
at the skill's Step 7 gate.

# Result

- `README.md` reduced from 1,030 lines to a ~95-line landing page (overview,
  quick start, the three commands, task table, doc map).
- New `docs/` tree: `README.md` (index), `tutorials/getting-started.md`,
  seven how-to guides (install/update, activate, manage projects, `tl`
  fallback, legacy migration, dev commands, troubleshooting),
  `reference/cli.md`, `reference/configuration.md`,
  `explanation/concepts.md`, and `development.md` (contributor content moved
  out of the README).
- Stale README claims dropped; previously undocumented commands covered
  (`project env`, `legacy inspect/migrate`, `project trust`,
  `config legacy-sourcing`, `--env`, `tw activate --legacy/--no-legacy`).
- Used the existing session branch `claude/taurworks-documentation-303036`
  (already fresh off master) rather than the skill's
  `<username>/chore/doc-work-*` naming.

# Validation

- Behavior verified against `src/taurworks/` and by running the CLI and the
  sourced `tw`/`tl` helpers in an isolated sandbox `HOME`, including the
  tutorial end to end.
- `scripts/format --check --diff`: pass. `scripts/lint`: pass.
- `scripts/test`: 404 tests OK.
- `lrh validate`: 0 errors, 0 warnings.
- Relative links and heading anchors across `README.md` and `docs/**/*.md`:
  0 broken.

# Follow-up

Behaviors found while verifying, documented as-is and not changed (candidate
work items; see the PR body for detail):

- Workspace resolution differs by command (`workspace set` is ignored by
  top-level `create`/`refresh` and by `tl`; `workspace show` does not report
  `$TAURWORKS_WORKSPACE`).
- `taurworks project refresh PATH` creates a missing target directory.
- `taurworks create --help` claims a setup script is created; none is.
- `tw activate` prints a `note:` on every activation of a project with no
  Conda environment.
- `tw shell refresh` does not refresh `tl.source`.
- `project/design/*.md` cite old README line numbers and section names.
