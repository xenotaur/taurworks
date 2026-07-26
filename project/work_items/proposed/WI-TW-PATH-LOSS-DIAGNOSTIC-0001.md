---
id: WI-TW-PATH-LOSS-DIAGNOSTIC-0001
title: Add Conda PATH-loss diagnostic to the tw shell helper
type: deliverable
status: proposed
blocked: false
blocked_reason: null
resolution: null
related_focus:
  - FOCUS-CURRENT
related_roadmap:
  - ROADMAP-INIT
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
  - "every `command taurworks ...` call site in src/taurworks/resources/shell/taurworks-shell.sh is guarded against the same PATH-loss failure, not only the outermost fallthrough: this includes tw activate's own calls before conda activate runs (project activate --shell), the calls reached after conda activate runs (legacy inspect / project trust set in the untrusted-legacy flow), tw shell refresh's shell print call, and tw help's delegation calls"
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
`src/taurworks/resources/shell/taurworks-shell.sh` has 8 distinct
`command taurworks ...` call sites, not just one: `tw activate`'s own
`project activate --shell` calls *before* `conda activate` runs (lines
~198, ~204); the `legacy inspect` / `project trust set` calls reached
*after* `conda activate` runs, during interactive untrusted-legacy
handling (lines ~78, ~87); `tw shell refresh`'s `shell print` call (line
~372); `tw help`'s two delegation calls (lines ~408, ~410); and the
general fallthrough delegation (line ~415). Review corrected an earlier,
narrower framing of this work item that guarded only the fallthrough and
the post-activation calls — a single check at the outermost
entry/fallthrough point alone would miss every other call site, including
ones reached *before* any Conda activation happens at all (`tw activate`'s
own initial calls) and ones in code paths (`tw shell refresh`, `tw help`)
that have nothing to do with activation. All 8 call sites are now in
scope.

Prior art check: before drafting this work item, no existing work item,
roadmap phase, or focus entry covered a PATH-loss diagnostic for `tw`
(`grep -rl "PATH-loss\|command not found\|conda.*taurworks.*resolve"`
across work items/roadmap/focus returned nothing at that time — that grep
will of course now match this file itself once it exists in the repo). At
that time no `FOCUS-*`/`ROADMAP-*` phase covered this; `project/focus/current_focus.md`
(`FOCUS-CURRENT`) and `project/roadmap/roadmap.md` (`ROADMAP-INIT` Phase 8)
have since been updated to cover this and the other three
`project/design/packaging_and_install.md` work items; `related_focus`/
`related_roadmap` above reflect that.

One of four work items drafted from `project/design/packaging_and_install.md`;
the others cover the `taurworks setup` command, the `bin/`/`taurscripts`
repo split, and the `--debug`/`TAURWORKS_DEBUG` flag audit. This WI is
scoped to the PATH-loss diagnostic only.

## Scope

- Add a resolvability check to `tw`'s fallthrough delegation path.
- Extend that guard to cover all `command taurworks ...` call sites in
  `src/taurworks/resources/shell/taurworks-shell.sh` — not only the
  fallthrough, and not only calls reached after `conda activate` runs: all
  8 call sites (`tw activate`'s pre-activation calls, its
  post-activation untrusted-legacy calls, `tw shell refresh`'s call, `tw
  help`'s two calls, and the fallthrough).
- Document the diagnostic's behavior in README.md.

## Required Changes

1. Add a `command -v taurworks` (or equivalent) resolvability check before
   `tw`'s fallthrough delegation (`command taurworks "$@"`, line ~415).
2. On failure, print a diagnostic to stderr naming the likely cause (an
   active Conda environment without `taurworks` installed) and a concrete
   next step (switch back, or check `which taurworks` / `pipx list`), then
   return non-zero.
3. Guard all 8 `command taurworks ...` call sites in
   `taurworks-shell.sh`, not only the fallthrough and not only calls
   reached after `conda activate` runs:
   - `tw activate`'s own `project activate --shell` calls, reached
     *before* any `conda activate` runs (lines ~198, ~204);
   - the `legacy inspect` / `project trust set` calls reached *after*
     `conda activate` runs, during interactive untrusted-legacy handling
     (lines ~78, ~87);
   - `tw shell refresh`'s `shell print` call (line ~372);
   - `tw help`'s two delegation calls (lines ~408, ~410);
   - the general fallthrough delegation (line ~415).

   Guard by either re-checking resolvability at each site, or by resolving
   and caching the executable path once per `tw` invocation (before any
   Conda activation that invocation might perform) and reusing that
   resolved reference at every call site in the same invocation. Exact
   mechanism is an implementation decision for this WI.
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
- Every `command taurworks ...` call site in
  `src/taurworks/resources/shell/taurworks-shell.sh` is guarded against
  the same PATH-loss failure — all 8 sites: `tw activate`'s pre-activation
  calls (`project activate --shell`), its post-activation untrusted-legacy
  calls (`legacy inspect` / `project trust set`), `tw shell refresh`'s
  `shell print` call, `tw help`'s two delegation calls, and the general
  fallthrough — not only the fallthrough and not only calls reached after
  `conda activate` runs.
- The guard adds no new subprocess spawn beyond what is already needed to
  check resolvability (e.g. a single `command -v taurworks` check, cached
  for the duration of one `tw` invocation where applicable).
- `tl` is verified to need no equivalent change, since it never depends on
  `taurworks` being resolvable.
- Tests or a documented manual dogfood procedure demonstrate the
  diagnostic firing when `taurworks` is hidden by a Conda environment
  switch, covering at minimum: plain `tw ...` fallthrough delegation,
  `tw activate` before any Conda activation, `tw activate` after `conda
  activate` runs (untrusted-legacy flow), `tw shell refresh`, and `tw
  help`.

## Validation

- ./scripts/format --check --diff
- ./scripts/lint
- ./scripts/test
- manual dogfood: activate a Conda environment without `taurworks`
  installed and confirm the diagnostic fires at each of the 8 call sites
  (fallthrough, tw activate pre- and post-Conda-activation, tw shell
  refresh, tw help)
- lrh validate
