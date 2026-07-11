---
id: WI-LEGACY-BATCH-MIGRATION-0001
title: One-time reviewed migration of the 12 legacy Admin projects to declarative config
type: operation
status: proposed
blocked: false
blocked_reason: null
resolution: null
---

# WI-LEGACY-BATCH-MIGRATION-0001: One-time reviewed migration of legacy Admin projects

## Summary
Write and run a one-time script that converts all 12 real
`<project>/Admin/project-setup.source` scripts in `~/Workspace` into
declarative `.taurworks/config.toml` activation data, with human-reviewed
dry-run diffs, without modifying or executing any legacy script.

## Problem / Context
`tw activate` Conda switching works end-to-end once
`[activation.environment]` exists in project config (verified in the
2026-07-11 dogfood session), but the shipped `taurworks legacy migrate`
matches 0 of the 12 real legacy scripts because 11 of them use variable
indirection (`ENVIRONMENT=X; conda activate $ENVIRONMENT; cd $WORKSPACE`) and
the 12th uses `cd $HOME/...`. The entire universe of legacy taurworks
projects is these 12; upgrading the general matcher is machinery for users
who do not exist (zero external users). A bespoke one-time run with human
review also catches data problems no matcher can, e.g.
`Imageworks (1)/Admin/project-setup.source` points at `~/Workspace/ImageWorks`
(the other project), and the review decides per project whether the
`source ~/bin/utilities.source` line (AWS login helpers) is a real need or
copypasta — determining the true scope of WI-TRUSTED-LEGACY-SOURCING-0001.

## Scope
- A one-time migration script in `bin/`, dry-run by default, `--apply` gated.
- One reviewed dry-run pass and one apply pass over the 12 legacy projects.
- An execution record capturing diffs, decisions, and the count of projects
  that still genuinely need script sourcing.

## Required Changes
1. Create `bin/migrate_legacy_projects.py`. It performs a preprocessing pass
   over each legacy script (resolve script-local `VAR=value` assignments when
   substituting `$VAR`; expand leading `~` and `$HOME`), then feeds the
   normalized lines through the existing merge logic
   (`src/taurworks/legacy.py` `_merge_legacy_matches_into_config`) and the
   safe writer (`src/taurworks/project_internals.py`
   `write_project_config`). Existing config values are never overwritten.
   `cd` targets are converted to project-root-relative `paths.working_dir`.
2. Run in dry-run mode across all legacy-admin projects; present per-project
   unified diffs of proposed config for owner review. Record per-project
   decisions (including whether `utilities.source` is genuinely needed).
3. Run with `--apply` for approved projects; verify each appears as
   initialized with a working_dir in `taurworks projects`.
4. Store the dry-run diffs, decisions, and final per-project outcomes in
   `project/executions/WI-LEGACY-BATCH-MIGRATION-0001/`.

## Non-Goals
- Do not modify, move, or delete any `Admin/project-setup.source` file — they
  remain as rollback and `tl` input.
- Do not execute or source any legacy script.
- Do not overwrite any existing `.taurworks/config.toml` value.
- Do not upgrade the general `taurworks legacy migrate` matcher — this
  operation replaces that planned work (YAGNI: zero external users).
- Do not implement script sourcing or trust records — that is
  WI-TRUSTED-LEGACY-SOURCING-0001.

## Acceptance Criteria
- Dry-run diffs for all 12 legacy projects were produced, reviewed by the
  owner, and archived in the execution record.
- After apply, each approved project shows as initialized and
  activation-eligible in `taurworks projects`.
- In a real shell, `tw activate LCATS` switches `$CONDA_DEFAULT_ENV` to
  `LCATS`, changes directory to `~/Workspace/LCATS/LCATS`, and prints the
  readiness message.
- Every `Admin/project-setup.source` file is byte-identical before and after.
- The execution record states how many projects still need arbitrary script
  sourcing (the sizing input for WI-TRUSTED-LEGACY-SOURCING-0001).

## Validation
- `lrh validate`
- `scripts/lint`
- `python bin/migrate_legacy_projects.py --dry-run` (diff output reviewed)
- `taurworks projects` (post-apply status check)
- Manual shell test: `tw activate LCATS` then `echo $CONDA_DEFAULT_ENV`

## Risk Notes
- Wrong-data hazard: at least one script (`Imageworks (1)`) contains paths
  pointing at a different project; the human review pass is the control.
- Some Conda environments named in scripts may no longer exist; migration
  records the config regardless (activation fails cleanly with the existing
  conda diagnostic), but the review should flag them.

## Dependencies / Order
Best run after WI-INTERIM-TL-PIPX-0001 (so `tl` exists as fallback during the
transition) and before WI-TRUSTED-LEGACY-SOURCING-0001 (whose scope it sizes).
No hard blocking dependency.
