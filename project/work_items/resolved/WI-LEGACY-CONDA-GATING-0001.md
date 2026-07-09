---
resolution: Legacy `taurworks refresh`/`create` Conda environment creation gated behind explicit `--create-env` opt-in; misleading activation guidance and help text fixed per review. Side-effect audit follow-up #2 resolved, #1 partially addressed. Implemented and merged in PR #63 (commit e9c9bf6).
blocked_reason: null
blocked: false
id: WI-LEGACY-CONDA-GATING-0001
title: Gate legacy Conda environment creation behind explicit opt-in
type: operation
status: resolved
owner: null
contributors: []
assigned_agents: []
related_focus: []
related_roadmap:
  - ROADMAP-INIT
related_workstreams: []
related_design:
  - project/audits/side_effects.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - implement_legacy_inspect_migrate
  - implement_trusted_hooks
  - automatic_legacy_script_sourcing
acceptance:
  - Legacy top-level `taurworks refresh NAME` and `taurworks create NAME` (and therefore `tw refresh`/`tw create`) no longer create a Conda environment by default; creation requires an explicit command or flag.
  - The explicit Conda-creation path is covered by unit tests distinguishing it from the default no-Conda path.
  - Repository-directory creation and the `.taurworks/project-setup.source` write in legacy `refresh`/`create` are explicitly unchanged by this item, not silently removed alongside Conda gating.
  - `tw activate`'s `eval` surface in `taurworks-shell.sh` is reviewed; either reduced or the decision to keep it is documented with rationale.
  - `project/audits/side_effects.md` is updated to mark follow-up #2 resolved and follow-up #1 as only partially addressed (Conda gating only).
  - `lrh validate` passes with 0 errors.
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/taurworks/manager.py
  - src/taurworks/cli.py
  - tests/manager_test.py
  - project/audits/side_effects.md
---

# WI-LEGACY-CONDA-GATING-0001: Gate legacy Conda environment creation behind explicit opt-in

## Summary
Stop legacy top-level `taurworks refresh`/`taurworks create` from creating a Conda environment by default, and work through the remaining low-risk follow-ups from the 2026-05-17 side-effect audit.

## Problem / Context
The post-merge side-effect audit (`project/audits/side_effects.md`, 2026-05-17) found that legacy `taurworks refresh NAME` — and therefore `tw refresh NAME`, since the shell helper delegates unknown commands to legacy `taurworks ...` — creates a Conda environment by default despite a name that sounds like safe, idempotent metadata repair. The audit called this "the most surprising finding" in the inventory. `taurworks create NAME` has the same behavior. No work item currently tracks fixing it. This item is scoped separately from `WI-ACTIVATION-CONFIG-0001`, which owns legacy inspect/migrate tooling and trusted hooks — those are explicitly out of scope here.

## Scope
- Stop legacy `taurworks refresh`/`taurworks create` from creating a Conda environment by default. This item does **not** make legacy `refresh`/`create` fully metadata-only: repository-directory creation and the legacy `.taurworks/project-setup.source` write are unchanged (see Non-Goals).
- Move Conda environment creation behind an explicit command or flag.
- Review (not necessarily eliminate) the `eval` surface in `tw activate`.
- Close out the audit document by marking resolved items and recording rationale for any left deferred.

## Required Changes
1. In `src/taurworks/manager.py`, change `refresh_project` and `create_project` so they no longer call `create_conda_environment` unless an explicit flag (e.g. `--create-env`) or a dedicated command is used.
2. Update `src/taurworks/cli.py` to expose the explicit opt-in for Conda creation on the legacy `refresh`/`create` commands.
3. Add/update unit tests in `tests/manager_test.py` (or the relevant CLI test file) covering both the new default (no Conda call) and the explicit opt-in path.
4. Review `src/taurworks/resources/shell/taurworks-shell.sh` for the `eval` surface described in the audit; document the review outcome (reduced, or kept with rationale) in `project/audits/side_effects.md`.
5. Update `project/audits/side_effects.md` follow-up recommendation #2 (Conda creation gating) to reflect resolution. Mark recommendation #1 (metadata-only `refresh`) as **partially** addressed: Conda creation is gated, but repository-directory creation and the `.taurworks/project-setup.source` write remain untouched pending a separate item (see Non-Goals / Open Questions). Add a note on #3-#7 status (most are already satisfied by current behavior per the audit's own findings).

## Non-Goals
- Do not implement `taurworks legacy inspect`/`legacy migrate` — that is `WI-ACTIVATION-CONFIG-0001` slices 4-5.
- Do not implement trusted user-script hooks — that is `WI-ACTIVATION-CONFIG-0001` slice 6.
- Do not add automatic sourcing of `Admin/project-setup.source` or any other legacy script.
- Do not remove or rename the legacy top-level `refresh`/`create` commands — compatibility is preserved.
- Do not change legacy `refresh`/`create`'s repository-directory creation or its `.taurworks/project-setup.source` write in this item. Making legacy `refresh`/`create` fully metadata-only (audit recommendation #1 in full) is a larger, more compatibility-sensitive change than Conda gating and is left as potential future work — see Open Questions.

## Acceptance Criteria
- Legacy `taurworks refresh NAME` / `taurworks create NAME` no longer call `conda create`/`conda env create` unless the explicit opt-in is used.
- New/updated tests pass and cover both the default (no Conda call) and explicit-opt-in paths.
- Legacy `taurworks refresh NAME` / `taurworks create NAME` still create the repository directory and write `.taurworks/project-setup.source` exactly as before this item — those side effects are explicitly unchanged, not silently removed alongside Conda gating.
- `project/audits/side_effects.md` reflects audit follow-up #2 as resolved and follow-up #1 as partially addressed (Conda only), not fully resolved.
- `lrh validate` passes with 0 errors.

## Open Questions
- Should a follow-up work item pursue full metadata-only `refresh`/`create` (removing/gating repository-directory creation and the `.taurworks/project-setup.source` write too), matching audit recommendation #1 in full? That is a larger compatibility-sensitive change deliberately deferred out of this item's scope.

## Validation
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Risk Notes
- Changing default behavior for `taurworks refresh`/`create` is a compatibility-sensitive change; anyone relying on the current default Conda-creation behavior needs a documented migration note (e.g. in release notes or `taurworks refresh --help`).
- Reducing the `eval` surface in `taurworks-shell.sh` risks breaking Conda/export activation if not carefully tested across the existing shell test coverage.
