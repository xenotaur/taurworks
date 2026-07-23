---
id: WI-TW-PATH-LOSS-DIAGNOSTIC-0001
title: Add Conda PATH-loss diagnostic to the tw shell helper
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
  - implement_bin_repo_split
  - implement_debug_flag
  - change_tw_activate_semantics
acceptance:
  - "when `taurworks` does not resolve on $PATH, `tw`'s initial delegation prints a diagnostic identifying the likely cause (an active Conda environment without taurworks installed) and a concrete next step, then returns non-zero, instead of a bare shell 'command not found'"
  - "every internal `command taurworks ...` call site inside tw activate (including those made after conda activate runs, e.g. the legacy inspect / project trust set calls in the untrusted-legacy flow) is guarded against the same PATH-loss failure, not only the outermost entry point"
  - "the guard adds no new subprocess spawn beyond what is already needed to check resolvability (e.g. a single `command -v taurworks` check, cached for the duration of one tw invocation where applicable)"
  - "tl is verified to need no equivalent change, since it never depends on taurworks being resolvable"
  - "tests or a documented manual dogfood procedure demonstrate the diagnostic firing when taurworks is hidden by a Conda environment switch, both at initial delegation and from within tw activate after conda activate runs"
artifacts_expected:
  - src/taurworks/resources/shell/taurworks-shell.sh
  - README.md
  - tests/ (shell-helper test coverage, if any exists) or a documented manual dogfood procedure
---

# WI-TW-PATH-LOSS-DIAGNOSTIC-0001: Add Conda PATH-loss diagnostic to the tw shell helper

## Summary

Add a diagnostic to the sourced `tw` shell function that detects when
`taurworks` does not resolve on `$PATH` — most commonly after a `conda
activate` into an environment that lacks the package — and prints a
pointed diagnostic instead of letting the shell's own bare `command not
found` be the only signal. This is Decisions #4 from
`project/design/packaging_and_install.md`.

## Problem / Context

Switching into a Conda environment that lacks `taurworks` currently fails
as a bare shell `command not found` with no indication of cause or fix.
`tw activate` itself runs `conda activate <name>` mid-function
(`src/taurworks/resources/shell/taurworks-shell.sh`) and makes further
internal `command taurworks ...` calls afterward — for example `legacy
inspect` and `project trust set` during interactive untrusted-legacy
handling (lines ~78, ~87), plus the `project activate --shell` calls (lines
~198, ~204) and the `shell print` call inside `tw shell refresh` (line
~372). A single check at the outermost entry/fallthrough point (line ~415)
would miss the case where the newly-activated environment hides
`taurworks` mid-function, after that entry check already passed.

Prior art check: no existing PATH-loss diagnostic or equivalent effort
found in-repo (`grep -rl "PATH-loss\|command not found\|conda.*taurworks.*resolve"`
across work items/roadmap/focus returns nothing). No `FOCUS-*`/`ROADMAP-*`
phase covers this yet; `related_focus`/`related_roadmap` left empty per
`WI-SHELL-HELPER-REFRESH-0001` precedent.

One of four work items drafted from `project/design/packaging_and_install.md`;
the others cover the `taurworks setup` command, the `bin/`/`taurscripts`
repo split, and the `--debug`/`TAURWORKS_DEBUG` flag audit. This WI is
scoped to the PATH-loss diagnostic only.

## Scope

- Add a resolvability check to `tw`'s initial delegation path.
- Extend that guard to cover internal `command taurworks ...` call sites
  reached after `conda activate` runs within `tw activate`, not only the
  outermost entry point.
- Document the diagnostic's behavior in README.md.

## Required Changes

1. Add a `command -v taurworks` (or equivalent) resolvability check before
   `tw`'s fallthrough delegation (`command taurworks "$@"`).
2. On failure, print a diagnostic to stderr naming the likely cause (an
   active Conda environment without `taurworks` installed) and a concrete
   next step (switch back, or check `which taurworks` / `pipx list`), then
   return non-zero.
3. Guard every internal `command taurworks ...` call site reached from
   within `tw activate` after `conda activate` runs — either by
   re-checking resolvability at each site, or by resolving and caching the
   executable path once before Conda activation happens in a given
   invocation and reusing that resolved reference for the rest of the
   invocation. Exact mechanism is an implementation decision for this WI.
4. Do not add a new subprocess spawn beyond what resolvability checking
   itself requires.
5. Verify `tl` needs no equivalent change (documented already in the
   design doc and `WI-TL-BREAKGLASS-0001`).
6. Update README.md to document the new diagnostic behavior.

## Non-Goals

- The `taurworks setup` command (separate WI).
- The `bin/`/`taurscripts` repo split (separate WI).
- The `--debug`/`TAURWORKS_DEBUG` flag and narration audit (separate WI).
- Any change to `tw activate`/`tw shell refresh`'s actual activation
  semantics — this WI only adds a diagnostic around PATH resolution, it
  does not change what activation does when `taurworks` *is* resolvable.
- Any change to `tl`.

## Acceptance Criteria

- When `taurworks` does not resolve on `$PATH`, `tw`'s initial delegation
  prints a diagnostic identifying the likely cause (an active Conda
  environment without `taurworks` installed) and a concrete next step,
  then returns non-zero, instead of a bare shell "command not found."
- Every internal `command taurworks ...` call site inside `tw activate`
  (including those made after `conda activate` runs, e.g. the `legacy
  inspect` / `project trust set` calls in the untrusted-legacy flow) is
  guarded against the same PATH-loss failure, not only the outermost entry
  point.
- The guard adds no new subprocess spawn beyond what is already needed to
  check resolvability (e.g. a single `command -v taurworks` check, cached
  for the duration of one `tw` invocation where applicable).
- `tl` is verified to need no equivalent change, since it never depends on
  `taurworks` being resolvable.
- Tests or a documented manual dogfood procedure demonstrate the
  diagnostic firing when `taurworks` is hidden by a Conda environment
  switch, both at initial delegation and from within `tw activate` after
  `conda activate` runs.

## Validation

- ./scripts/format --check --diff
- ./scripts/lint
- ./scripts/test
- manual dogfood: activate a Conda environment without `taurworks`
  installed and confirm the diagnostic fires both at plain `tw ...`
  delegation and from within `tw activate` after `conda activate` runs
- lrh validate
