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
  - "--keep-tl-fallback moves Admin/project-setup.source to .taurworks/project-setup.source only when the migration is verified fully complete: unsupported_count == 0, manual_review empty, and every skipped entry's existing value verified equal to what the legacy line would have set"
  - "A script with a duplicate or conflicting line (unsupported_count == 0 but non-empty manual_review or a non-equivalent skipped entry) is treated as incomplete and left untouched, not silently retired"
  - "Retirement fires on a rerun against a project already fully configured from an earlier invocation (empty patch this run), not only when this invocation wrote a new patch"
  - "An existing, non-identical file already at .taurworks/project-setup.source blocks the move with a clear message; neither file is mutated"
  - "A partial match leaves Admin/project-setup.source untouched and reports a clear message, never a silent partial retirement"
  - "Omitting the flag reproduces today's exact behavior: config.toml only, Admin/project-setup.source untouched"
  - "New tests cover full-match, partial-match (including duplicate/conflict), flag-omitted, rerun-after-earlier-migration, and destination-collision cases"
  - "activation_extension.md documents the new flag, the completeness check, and the inherited variable-indirection matcher limitation this item does not fix"
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
`--keep-tl-fallback` flag that, only once the migration is verified fully
complete — not just `unsupported_count == 0`, but also free of merge-time
duplicates or conflicts silently diverted into `manual_review`/`skipped` —
moves the original `Admin/project-setup.source` to
`.taurworks/project-setup.source` (`tl`'s existing second lookup slot),
refusing to overwrite a pre-existing, non-identical file at that
destination, automating the manual retirement recipe already documented in
`README.md` for future migrations of simple scripts.

## Problem / Context
During 2026-07-22 dogfooding, 11 real projects (`LCATS`, `EmbodiedAI`,
`CentaursGuide`, `ImageWorks`, `LogicalRoboticsHarness`, `Narramorph`,
`Novarc`, `ProsocialRobotics`, `PythonGames`, `Taxman`, `Taurcode`) were
found with a fully-migrated `.taurworks/config.toml` sitting alongside a
now-redundant `Admin/project-setup.source`. (A twelfth project, `Taurworks`,
was found with a related but distinct bug in the same dogfooding session — a
stale, case-mismatched `.taurworks/project-setup.source` companion, not an
unretired `Admin/` script — and is not part of this item's scope.) `tw
activate` still detects the lingering `Admin/` file and offers trust-gated
sourcing, which risks silently duplicating already-declarative behavior if
ever trusted — exactly what happened for `LCATS` before this was caught.
Each was retired by hand: move the script to
`.taurworks/project-setup.source` (keeping `tl`'s break-glass fallback
working) plus `taurworks project trust unset NAME`; the recipe is now
documented in `README.md`. `taurworks legacy migrate --apply`
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
- When set, only retire the script once the migration is verified fully
  complete: `unsupported_count == 0` **and** no merge-time
  duplicates/conflicts left in `manual_review`, and every `skipped` entry's
  existing config value verified equal to what the legacy line would have
  set (not merely "already present").
- Retirement must be reachable independently of whether *this* invocation
  wrote a new config patch — a rerun against a project already fully
  migrated in an earlier run (the common case, since `--apply` without the
  flag is today's existing default path) must still be able to retire.
- Move (not copy) `Admin/project-setup.source` to
  `.taurworks/project-setup.source`, refusing to overwrite an existing,
  non-identical file at that destination (a pre-existing, unrelated file
  can legitimately be there — see Required Change 3).
- Do not bundle `taurworks project trust unset` into this flag — it stays a
  separate, explicit step, exactly as the README recipe already documents.
- Document the flag, the completeness check, and the inherited matcher
  limitation in `activation_extension.md`.

## Required Changes
1. `src/taurworks/legacy.py`: add a migration-completeness check that is
   stronger than `unsupported_count == 0` alone. The per-line parse pass
   (`gather_legacy_inspect_diagnostics`) and the merge pass
   (`_merge_legacy_matches_into_config`, `legacy.py:293-441`) are separate:
   a script with duplicate or conflicting lines (e.g. two `conda activate`
   statements, or a legacy export whose value conflicts with an
   already-configured one) parses as fully "supported" per line
   (`unsupported_count == 0`) but the duplicate/conflict is diverted into
   `manual_review`/`skipped` during merging without ever being represented
   in `config.toml` — neither case increments `unsupported_count`. Add a
   function that returns "fully covered" only when `manual_review` is empty
   **and** every `skipped` entry's existing config value is verified equal
   to what the corresponding legacy line would have set; test it
   independently of `--keep-tl-fallback`.
2. `src/taurworks/legacy.py`: make retirement reachable on its own, not
   nested after `config_written = True`. `gather_legacy_migrate_diagnostics`
   returns early at `legacy.py:478-482` ("no unambiguous legacy patterns to
   migrate") whenever `merge_result["patch"]` is empty — exactly what
   happens on a rerun against a project whose `config.toml` already has
   everything configured (e.g. a prior config-only migration via the
   flag-omitted path). Restructure so the completeness check and retirement
   from Required Change 1 run as an independent step whenever
   `--keep-tl-fallback` is set, regardless of whether this specific
   invocation produced a new patch.
3. `src/taurworks/legacy.py`: guard the move against an existing
   destination. `.taurworks/project-setup.source` may already exist for
   reasons unrelated to this item's retirement flow — legacy `create`/
   `refresh` historically wrote this exact path before
   `WI-ACTIVATION-PRODUCERS-0001` converged them onto `config.toml`
   (`WI-ACTIVATION-PRODUCERS-0001:46-50`). Require the destination to be
   absent, or byte-identical to the source, before moving; otherwise fail
   safely with a clear message and mutate neither file.
4. `src/taurworks/cli.py`: add the `--keep-tl-fallback` flag to the
   `legacy migrate` subparser and thread it through to
   `gather_legacy_migrate_diagnostics`.
5. `tests/legacy_test.py`: add cases for (a) a fully literal script with the
   flag set → script moved, target content matches, `Admin/` no longer has
   the file; (b) a script with at least one unsupported line and the flag
   set → no-op, clear message, script untouched; (c) a script with a
   duplicate/conflicting line (`unsupported_count == 0` but non-empty
   `manual_review` or a non-equivalent `skipped` entry) and the flag set →
   no-op, script untouched — this is the case comment 2 identifies as
   currently unguarded; (d) flag omitted → today's exact unchanged
   behavior; (e) rerun against a project already fully configured from an
   earlier run (empty patch this invocation) with the flag set → retirement
   still fires; (f) an existing, non-identical file already at
   `.taurworks/project-setup.source` with the flag set → fails safely,
   neither file mutated.
6. `project/design/activation_extension.md`: document `--keep-tl-fallback`,
   the completeness check (beyond `unsupported_count`), the
   independent-of-this-invocation retirement path, the destination-collision
   guard, and the inherited variable-indirection matcher limitation this
   item does not fix, under "Legacy `Admin/project-setup.source` migration",
   with a pointer to the manual recipe in `README.md` for scripts that don't
   qualify.

## Non-Goals
- Do not upgrade the `legacy migrate` matcher to handle variable indirection
  — explicitly out of scope per `project/roadmap/roadmap.md:49-51`
  ("General-purpose `legacy migrate` matcher upgrades... not planned").
- Do not bundle `taurworks project trust unset` into `--keep-tl-fallback` —
  trust revocation remains a separate, explicitly-run step.
- Do not retroactively touch any of the 11 projects already retired by hand
  during 2026-07-22 dogfooding (or `Taurworks`, fixed separately for its
  distinct case-mismatch bug).
- Do not change `tl`'s lookup mechanics (`sourceme/aliases.source`) in any
  way — respects `WI-TL-BREAKGLASS-0001`'s explicit "do not change the
  lookup order or sourcing mechanics."
- Do not change `taurworks legacy inspect`'s read-only diagnostic behavior.

## Acceptance Criteria
- `--keep-tl-fallback` moves `Admin/project-setup.source` to
  `.taurworks/project-setup.source` only when the migration is verified
  fully complete: `unsupported_count == 0`, `manual_review` empty, and every
  `skipped` entry's existing config value verified equal to what the legacy
  line would have set.
- A script with a duplicate or conflicting line — which parses as
  `unsupported_count == 0` but diverts to `manual_review` or a
  non-equivalent `skipped` entry during merging — is correctly treated as
  incomplete and left untouched, not silently retired.
- Retirement fires on a rerun against a project already fully configured
  from an earlier invocation (empty patch this run), not only when this
  specific invocation just wrote a new patch.
- An existing, non-identical file already at `.taurworks/project-setup.source`
  blocks the move with a clear message; neither file is mutated.
- A partial match leaves `Admin/project-setup.source` untouched and reports
  a clear message — never a silent partial retirement (mirrors the
  `EmbodiedAI` lesson from 2026-07-22 dogfooding, where an incomplete
  migration was nearly retired with a `CREDENTIALS` export silently lost).
- Omitting the flag reproduces today's exact behavior: `config.toml`
  written, `Admin/project-setup.source` untouched.
- New tests cover: full match, partial match (including a duplicate/conflict
  case), flag-omitted, rerun-after-earlier-migration, and
  destination-collision cases.
- `activation_extension.md` documents the flag, the completeness check, and
  the inherited variable-indirection matcher limitation.
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
- Given the matcher's variable-indirection gap, expect the completeness
  check to rarely pass for real-world scripts as currently observed in this
  workspace — this item's near-term practical yield is low by design, not a
  bug to route around. Value is forward-looking (simpler future scripts, or
  a future matcher improvement, which remains a separate decision).
- The completeness check (Required Change 1) is more subtle than a single
  field comparison: verifying a `skipped` entry's existing value truly
  equals what the legacy line would have set requires comparing against the
  same `proposed_config` value the merge function already computes for
  applied fields, not just checking presence. Get this wrong and the gate
  degrades back to the original, insufficient `unsupported_count == 0`
  check found during PR review.
- Moving (not copying) the script must not leave a partially-written or
  duplicated state if interrupted mid-operation; a plain filesystem rename
  is lower-risk than a multi-step write (contrast with `tw shell refresh`'s
  temp-file-then-rename need for content it generates itself, per
  `project/design/shell_helper_refresh.md`), but the implementation should
  still confirm the move is atomic on the target filesystem or use an
  equivalent write-then-remove-original safeguard.
- The destination-collision guard (Required Change 3) must compare content,
  not just existence — an empty or placeholder file at
  `.taurworks/project-setup.source` is still a collision, not something
  safe to overwrite silently.
