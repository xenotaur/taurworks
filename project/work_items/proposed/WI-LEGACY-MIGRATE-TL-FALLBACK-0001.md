---
resolution: null
blocked_reason: null
blocked: false
id: WI-LEGACY-MIGRATE-TL-FALLBACK-0001
title: Automate `tl`-compatible retirement in `taurworks legacy migrate --apply`
type: deliverable
status: proposed
owner: null
contributors: []
assigned_agents: []
related_focus:
  - FOCUS-CURRENT
related_roadmap:
  - ROADMAP-INIT
related_workstreams: []
related_design:
  - project/design/activation_extension.md
  - README.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - upgrade_legacy_migrate_matcher
acceptance:
  - "--keep-tl-fallback moves Admin/project-setup.source to .taurworks/project-setup.source only when unsupported_count == 0 (a fully literal, fully migrated script)"
  - "A partial match (unsupported_count > 0) leaves Admin/project-setup.source untouched and reports a clear message, never a silent partial retirement"
  - "Omitting the flag reproduces today's exact behavior: config.toml only, Admin/project-setup.source untouched"
  - "New tests cover full-match, partial-match, and flag-omitted cases"
  - "activation_extension.md documents the new flag and the inherited variable-indirection matcher limitation this item does not fix"
  - "scripts/test passes; lrh validate introduces no new errors"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/taurworks/legacy.py
  - src/taurworks/cli.py
  - tests/legacy_test.py
  - project/design/activation_extension.md
---

# WI-LEGACY-MIGRATE-TL-FALLBACK-0001: Automate `tl`-compatible retirement in `taurworks legacy migrate --apply`

## Summary
Extend `taurworks legacy migrate PROJECT --apply` with an opt-in
`--keep-tl-fallback` flag that, only when the migration is fully literal
(`unsupported_count == 0`), moves the original `Admin/project-setup.source`
to `.taurworks/project-setup.source` — `tl`'s existing second lookup slot —
automating the manual retirement recipe already documented in `README.md`
for future migrations of simple scripts.

## Problem / Context
During 2026-07-22 dogfooding, 10 real projects (`LCATS`, `EmbodiedAI`,
`Taurworks`, `CentaursGuide`, `ImageWorks`, `LogicalRoboticsHarness`,
`Narramorph`, `Novarc`, `ProsocialRobotics`, `PythonGames`, `Taxman`,
`Taurcode`) were found with a fully-migrated `.taurworks/config.toml` sitting
alongside a now-redundant `Admin/project-setup.source`. `tw activate` still
detects that file and offers trust-gated sourcing, which risks silently
duplicating already-declarative behavior if ever trusted — exactly what
happened for `LCATS` before this was caught. Each was retired by hand: move
the script to `.taurworks/project-setup.source` (keeping `tl`'s break-glass
fallback working) plus `taurworks project trust unset NAME`; the recipe is
now documented in `README.md`. `taurworks legacy migrate --apply`
(`src/taurworks/legacy.py:446-505`) only ever writes `config.toml` — it never
touches the original script — so every future migration lands in the same
state by default, requiring the same manual recipe again.

**Prior-art check:**
- *Duplication search* — in-repo: no existing implementation; `--apply`'s
  only side effect today is writing `config.toml` (confirmed by reading
  `legacy.py:446-505` directly). Sibling repos: none identified. External
  libraries: none applicable (taurworks-specific behavior). Recommendation:
  proceed.
- *Demand search* — no other work item or design doc requests this
  automation; only adjacent, already-resolved work
  (`WI-LEGACY-BATCH-MIGRATION-0001`, `WI-TL-BREAKGLASS-0001`,
  `WI-SHELL-HELPER-REFRESH-0001`) touches related ground without
  implementing it. Recommendation: no action.

**Known limitation, stated honestly rather than routed around:** per
`project/roadmap/roadmap.md:20,30-34,49-51`, the `legacy migrate` matcher
already fails to match any of the 12 real legacy scripts because they use
variable indirection (`VAR=value` assigned first, referenced later as
`$VAR`), and a general matcher upgrade is explicitly out of scope ("not
planned, zero external users"). This work item does not touch the matcher —
it only acts on the matcher's *existing* per-line classification, gated on
full literal coverage. In this workspace, essentially no real script would
trigger the new flag today; the value is for future, simpler legacy scripts
(or a future public-facing matcher improvement), not a fix for the current
corpus.

## Scope
- Add `--keep-tl-fallback` to `taurworks legacy migrate PROJECT --apply`.
- When set and the migration fully covers the script
  (`unsupported_count == 0`), move (not copy) `Admin/project-setup.source`
  to `.taurworks/project-setup.source`.
- Do not bundle `taurworks project trust unset` into this flag — it stays a
  separate, explicit step, exactly as the README recipe already documents.
- Document the flag and the inherited matcher limitation in
  `activation_extension.md`.

## Required Changes
1. `src/taurworks/legacy.py`: add `keep_tl_fallback: bool = False` to
   `gather_legacy_migrate_diagnostics` (`legacy.py:446-505`). After
   `config_written = True`, if the flag is set, `unsupported_count == 0`,
   and `Admin/project-setup.source` exists, move it to
   `.taurworks/project-setup.source` and record the action (path moved
   from/to) in the returned diagnostics dict.
2. `src/taurworks/cli.py`: add the `--keep-tl-fallback` flag to the
   `legacy migrate` subparser and thread it through to
   `gather_legacy_migrate_diagnostics`.
3. `tests/legacy_test.py`: add cases for (a) a fully literal script with the
   flag set → script moved, target file content matches, `Admin/` no longer
   has the file; (b) a script with at least one unsupported line and the
   flag set → no-op, clear message, `Admin/project-setup.source` untouched;
   (c) flag omitted → today's exact unchanged behavior (config.toml written
   only, `Admin/project-setup.source` untouched regardless of match
   completeness).
4. `project/design/activation_extension.md`: document `--keep-tl-fallback`
   under "Legacy `Admin/project-setup.source` migration", including the
   variable-indirection matcher limitation this item inherits rather than
   fixes, and a pointer to the manual recipe in `README.md` for scripts that
   don't qualify.

## Non-Goals
- Do not upgrade the `legacy migrate` matcher to handle variable indirection
  — explicitly out of scope per `project/roadmap/roadmap.md:49-51`
  ("General-purpose `legacy migrate` matcher upgrades... not planned").
- Do not bundle `taurworks project trust unset` into `--keep-tl-fallback` —
  trust revocation remains a separate, explicitly-run step.
- Do not retroactively touch any of the 10 projects already retired by hand
  during 2026-07-22 dogfooding.
- Do not change `tl`'s lookup mechanics (`sourceme/aliases.source`) in any
  way — respects `WI-TL-BREAKGLASS-0001`'s explicit "do not change the
  lookup order or sourcing mechanics."
- Do not change `taurworks legacy inspect`'s read-only diagnostic behavior.

## Acceptance Criteria
- `--keep-tl-fallback` moves `Admin/project-setup.source` to
  `.taurworks/project-setup.source` only when `unsupported_count == 0`.
- A partial match (`unsupported_count > 0`) leaves
  `Admin/project-setup.source` untouched and reports a clear message —
  never a silent partial retirement (mirrors the `EmbodiedAI` lesson from
  2026-07-22 dogfooding, where an incomplete migration was nearly retired
  with a `CREDENTIALS` export silently lost).
- Omitting the flag reproduces today's exact behavior: `config.toml`
  written, `Admin/project-setup.source` untouched.
- New tests cover full-match, partial-match, and flag-omitted cases.
- `activation_extension.md` documents the flag and the inherited
  variable-indirection matcher limitation.
- `scripts/test` passes; `lrh validate` introduces no new errors.

## Validation
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`

## Related Workstream and Designs
- Design: `project/design/activation_extension.md` (governs `legacy
  inspect`/`migrate` scope and non-goals)
- Related: `README.md` (documents the manual retirement recipe this item
  automates for the subset of scripts the matcher can fully parse)
- Roadmap context: `project/roadmap/roadmap.md:20,30-34,49-51` (the
  variable-indirection matcher limitation and its explicit out-of-scope
  status)

## Risk Notes
- Given the matcher's variable-indirection gap, expect
  `unsupported_count == 0` to rarely hold for real-world scripts as
  currently observed in this workspace — this item's near-term practical
  yield is low by design, not a bug to route around. Value is forward-looking
  (simpler future scripts, or a future matcher improvement, which remains a
  separate decision).
- Moving (not copying) the script must not leave a partially-written or
  duplicated state if interrupted mid-operation; a plain filesystem rename
  is lower-risk than a multi-step write (contrast with `tw shell refresh`'s
  temp-file-then-rename need for content it generates itself, per
  `project/design/shell_helper_refresh.md`), but the implementation should
  still confirm the move is atomic on the target filesystem or use an
  equivalent write-then-remove-original safeguard.
