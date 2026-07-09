---
id: WI-ACTIVATION-CONFIG-0001
title: Implement declarative activation config
type: deliverable
status: active
blocked: false
blocked_reason: null
resolution: null
---

# WI-ACTIVATION-CONFIG-0001: Implement declarative activation config

## Status
Slices 1-3 (activation message, exports, Conda activation) are implemented and
merged. Remaining active scope is slices 4-6: legacy inspect, legacy migrate,
and trusted hooks.

## Objective
Implement the safe declarative subset of legacy activation behavior from
`.taurworks/config.toml` without automatically sourcing arbitrary project
scripts.

## Design source
Use `project/design/activation_extension.md` as the source of truth for this work
item. The design covers:

- `[activation].message` readiness text;
- `[activation.environment] type = "conda"` and `name` as the only initially
  designed environment activation strategy;
- `[activation.exports]` literal environment variable data with validation,
  shell quoting, documented leading `~` expansion, secret-conscious output, and
  a separate machine-readable payload channel for `tw activate`;
- future trusted hooks behind explicit opt-in only;
- legacy inspect/migrate commands that prefer declarative fields over copying or
  executing scripts.

## Non-goals
This work item must not introduce:

- automatic legacy `Admin/project-setup.source` sourcing;
- arbitrary user-command execution by default;
- shell startup-file edits;
- automatic `conda init`;
- secret values in normal diagnostic output;
- shell-state mutation from `taurworks project activate --print`;
- evaluating human-formatted `--print` diagnostics as shell activation payload.

## Problem
Legacy Taurworks-style projects encode setup behavior in `Admin/project-setup.source`
(Conda activation, `export` assignments, `cd`, readiness messages). Taurworks
currently only detects that this file exists (`classify_project_entry` in
`manager.py`) — it does not help users extract or migrate that behavior into
declarative `.taurworks/config.toml` fields. Without inspect/migrate tooling,
legacy-admin projects have no safe path forward except manual config authoring
or continuing to rely on unsourced legacy scripts.

## Scope
- Implement `taurworks legacy inspect PROJECT` (slice 4): conservative,
  read-only extraction and reporting of common legacy patterns from
  `Admin/project-setup.source`.
- Implement `taurworks legacy migrate PROJECT --apply` (slice 5): write
  declarative `.taurworks/config.toml` fields for unambiguous detected
  patterns, on explicit user opt-in only.

## Out of Scope
- Slice 6 (trusted hooks) — explicitly deferred until legacy inspect/migrate
  has been dogfooded, per this design's own Option D recommendation and the
  roadmap's "Out of scope now" list. Track as a separate future work item once
  dogfooding feedback exists.
- Automatic fallback sourcing of `Admin/project-setup.source` (already
  excluded by `## Non-goals` above).
- Any change to the declarative activation schema itself (message, exports,
  Conda environment) — slices 1-3 are done and out of scope for this
  refinement.

## Required Changes
1. Add `taurworks legacy inspect PROJECT` that:
   - locates the legacy script through the existing project resolver;
   - detects `conda activate NAME`, simple `export KEY=value` assignments,
     `cd PATH`, and readiness `echo`/`printf` messages;
   - proposes corresponding `.taurworks/config.toml` fields when extraction is
     unambiguous;
   - reports unsupported constructs (dynamic shell, sourced files, function
     calls, command substitutions, aliases, conditionals) as requiring manual
     review;
   - redacts likely-sensitive export values by default while still showing
     variable names and detection status;
   - never executes or sources the script.
2. Add `taurworks legacy migrate PROJECT --apply` that:
   - writes changes only when `--apply` is passed;
   - prefers declarative config fields over copying scripts;
   - preserves existing `.taurworks/config.toml` values unless the user
     explicitly opts to replace them;
   - shows a reviewable diff or summary before applying;
   - leaves unsupported shell behavior as manual follow-up notes;
   - never enables hook execution or copies scripts into a trusted-hook
     location (slice 6 is out of scope).
3. Wire both subcommands into `src/taurworks/cli.py` under a new `legacy`
   subparser namespace.

## Likely Files
Inferred module layout from the repo's existing one-module-per-feature
convention (`manager.py`, `project_internals.py`, `project_registry.py`,
`project_resolution.py`, `global_config.py`) — not dictated by any artifact;
confirm before implementation.

- `src/taurworks/legacy.py` (new) — parsing/detection/migration logic
- `src/taurworks/cli.py` — new `legacy inspect` / `legacy migrate` subparsers
- `tests/legacy_test.py` (new) — unit tests for parsing, validation,
  rendering, failure modes, safety boundaries
- `project/design/activation_extension.md` — update implementation-status
  notes for slices 4-5 once shipped

## Validation
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- Unit tests covering: pattern parsing, validation, rendering, failure modes,
  and safety boundaries (per `## Validation expectations` below), for both
  `legacy inspect` and `legacy migrate --apply`

## Acceptance Criteria
- `taurworks legacy inspect PROJECT` never executes or sources the legacy
  script and is safe to run repeatedly (read-only).
- `taurworks legacy inspect PROJECT` correctly detects and reports the four
  named pattern types, and flags unsupported constructs as manual-review
  items rather than silently dropping them.
- `taurworks legacy migrate PROJECT --apply` makes no changes without
  `--apply`, and preserves pre-existing `.taurworks/config.toml` values not
  explicitly replaced.
- Sensitive export values are redacted in `legacy inspect` output by default.
- New/updated tests cover both commands' parsing, validation, and failure
  paths.
- `lrh validate` passes with 0 errors.

## Open Questions
- Exact `Likely Files` module name/location (`legacy.py` vs. extending
  `project_internals.py`) is inferred from repo convention, not specified —
  confirm before implementation.
- Should `legacy migrate --apply` require an interactive confirmation prompt,
  or is showing the diff and requiring the explicit `--apply` flag sufficient?
  Not addressed by the design doc.
- Exact redaction heuristic for "likely sensitive" export values (env var
  name patterns? entropy check?) is not specified in the design doc.
- Should `legacy inspect`/`legacy migrate` gain a `--dry-run` synonym for
  discoverability, or is inspect-then-migrate the intended two-step UX? Design
  doc implies the latter but doesn't rule out the former.

## Implementation slices
1. Implement activation message only. **Done.**
2. Implement exports with a separate machine-readable payload channel for
   `tw activate` and redacted human diagnostics. **Done.**
3. Implement Conda activation in `tw activate` without running `conda init`.
   **Done.**
4. Implement `taurworks legacy inspect PROJECT` as conservative read-only
   extraction. **Remaining.**
5. Implement `taurworks legacy migrate PROJECT --apply` for simple scripts while
   preserving existing config and requiring manual review for unsupported shell.
   **Remaining.**
6. Design and implement trusted hooks only after declarative activation has been
   dogfooded. **Remaining.**

## Validation expectations
Each implementation slice should include unit tests for parsing, validation,
rendering, failure modes, and safety boundaries, plus the repository standard
format/lint/test checks.
