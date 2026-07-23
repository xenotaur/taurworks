---
id: WI-BIN-REPO-SPLIT-0001
title: Split bin/ out of taurworks; relocate migrate_legacy_projects.py; wire sourceme/ into packaging
type: deliverable
status: proposed
blocked: false
blocked_reason: null
resolution: null
related_focus: []
related_roadmap: []
related_workstreams: []
depends_on: []
blocked_by: []
forbidden_actions:
  - force_push
  - delete_branch
  - implement_setup_command
  - implement_path_loss_diagnostic
  - implement_debug_flag
  - delete_migrate_legacy_projects_functionality
acceptance:
  - "bin/'s actual usage is audited (who/what depends on each file) and the disposition decision (taurscripts package vs. deletion) is recorded with rationale in this WI's resolution"
  - "migrate_legacy_projects.py is relocated under the taurworks package boundary (not bin/), and tests/migrate_legacy_projects_test.py is updated to the new path and still passes"
  - "all other bin/ contents (personal dotfiles: dot.bashrc, byobu configs, screen wrappers, etc.) are removed from the taurworks repo — either deleted or moved to a separate taurscripts location per the audit decision — so bin/ no longer mixes personal material with taurworks-specific code"
  - "sourceme/'s tl-delivery files are wired into setup.py's package_data (or equivalent packaging mechanism) so future tooling can place them"
  - "README.md's \"Legacy shell utility inventory (historical)\" section is updated to reflect the new state"
artifacts_expected:
  - bin/ (removed or relocated contents)
  - src/taurworks/ (migrate_legacy_projects.py's new home)
  - tests/migrate_legacy_projects_test.py
  - setup.py
  - README.md
---

# WI-BIN-REPO-SPLIT-0001: Split bin/ out of taurworks; relocate migrate_legacy_projects.py; wire sourceme/ into packaging

## Summary

Split `bin/`'s unrelated personal dotfile material out of the `taurworks`
repo, while exempting and relocating `migrate_legacy_projects.py` (which
imports `taurworks` internals and is imported by a test) to stay under the
`taurworks` package boundary, and wire `sourceme/`'s `tl`-delivery files
into `setup.py`'s `package_data`. This is Decisions #2 from
`project/design/packaging_and_install.md`.

## Problem / Context

`bin/` currently mixes two unrelated concerns: 26 files of pre-taurworks
personal dotfile material (`dot.bashrc`, byobu configs, screen wrappers,
etc.) with no dependency on the `taurworks` package, and one file
(`migrate_legacy_projects.py`) that does import `taurworks.legacy`,
`taurworks.manager`, and `taurworks.project_internals`, and is imported by
`tests/migrate_legacy_projects_test.py` by file path. `sourceme/` (`tl`'s
actual delivery mechanism) is not currently wired into `setup.py`'s
`package_data`, which only lists `resources/shell/taurworks-shell.sh`.

Prior art check: no existing bin/taurscripts split effort found in-repo
(`grep -rl "taurscripts\|bin/ split\|migrate_legacy_projects"` across work
items/roadmap/focus returns only `WI-LEGACY-BATCH-MIGRATION-0001`, which
originally created `migrate_legacy_projects.py` — not a duplicate of this
split). No `FOCUS-*`/`ROADMAP-*` phase covers this yet;
`related_focus`/`related_roadmap` left empty per
`WI-SHELL-HELPER-REFRESH-0001` precedent.

One of four work items drafted from `project/design/packaging_and_install.md`;
the others cover the `taurworks setup` command, the Conda PATH-loss
diagnostic, and the `--debug`/`TAURWORKS_DEBUG` flag audit. This WI is
scoped to the repo-split and packaging-wiring piece only.

## Scope

- Audit `bin/`'s actual usage (in-repo and, as far as can be determined,
  outside it) to decide `taurscripts` package vs. deletion for the
  non-`migrate_legacy_projects.py` contents.
- Relocate `migrate_legacy_projects.py` under the `taurworks` boundary.
- Wire `sourceme/` into `setup.py`'s `package_data`.
- Update README.md's legacy-utility-inventory section.

## Required Changes

1. Audit `bin/`'s contents for real external usage; record findings.
2. Based on the audit, either create a minimal `taurscripts` package for
   the unrelated dotfile material, or delete it — do not assume without
   checking.
3. Move `migrate_legacy_projects.py` to a location under `src/taurworks/`
   (or an equivalent in-package tools location); update
   `tests/migrate_legacy_projects_test.py`'s import path accordingly.
4. Add `sourceme/`'s files to `setup.py`'s `package_data`.
5. Update README.md's "Legacy shell utility inventory (historical)"
   section.

## Non-Goals

- The `taurworks setup` command itself (separate WI) — this WI only wires
  packaging; it does not implement the command that consumes it.
- The Conda PATH-loss diagnostic in `tw` (separate WI).
- The `--debug`/`TAURWORKS_DEBUG` flag and narration audit (separate WI).
- Removing or changing `migrate_legacy_projects.py`'s functionality —
  relocation only.

## Acceptance Criteria

- `bin/`'s actual usage is audited (who/what depends on each file) and the
  disposition decision (`taurscripts` package vs. deletion) is recorded
  with rationale in this WI's resolution.
- `migrate_legacy_projects.py` is relocated under the `taurworks` package
  boundary (not `bin/`), and `tests/migrate_legacy_projects_test.py` is
  updated to the new path and still passes.
- All other `bin/` contents (personal dotfiles: `dot.bashrc`, byobu
  configs, screen wrappers, etc.) are removed from the taurworks repo —
  either deleted or moved to a separate `taurscripts` location per the
  audit decision — so `bin/` no longer mixes personal material with
  taurworks-specific code.
- `sourceme/`'s `tl`-delivery files are wired into `setup.py`'s
  `package_data` (or equivalent packaging mechanism) so future tooling can
  place them.
- README.md's "Legacy shell utility inventory (historical)" section is
  updated to reflect the new state.

## Validation

- ./scripts/format --check --diff
- ./scripts/lint
- ./scripts/test
- lrh validate
