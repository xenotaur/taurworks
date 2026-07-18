---
id: WI-TL-BREAKGLASS-0001
title: Simplify tl to a permanent break-glass fallback; document tl/tw/taurworks; fix small dogfood-audit gaps
type: deliverable
status: proposed
blocked: false
blocked_reason: null
resolution: null
---

# WI-TL-BREAKGLASS-0001: tl break-glass simplification, tl/tw/taurworks docs, small dogfood-audit fixes

## Summary
Simplify `tl`'s calling convention to `tl NAME` (drop the `activate` verb;
no new logic), reframe it in code and docs as a permanent, intentionally
dumb "emergency break-glass" fallback rather than a temporary bridge to be
retired, write one unified explanation of the `tl`/`tw`/`taurworks`
three-tier relationship, and fix two small correctness/discoverability gaps
found during live dogfooding of the fully-shipped dogfood-recovery-plan.

## Problem / Context
The 2026-07-11 through 2026-07-18 dogfood sessions shipped and live-verified
the full activation stack (WI-INTERIM-TL-PIPX-0001 through
WI-TRUSTED-LEGACY-SOURCING-0001, PRs #67-70). A follow-up live
re-verification pass on 2026-07-18 surfaced four things:

1. A proposal to make `tl` delegate to `tw` when available was considered
   and rejected: `tw` being merely *defined* in a shell doesn't mean it's
   *current* (the stale-shell-helper problem found the same day proved a
   `tw` function can silently lag the installed package by several PRs with
   no error), and delegating would make `tl NAME` behave differently in
   different shells based on invisible ambient state. `tl`'s calling
   convention (`tl activate NAME`) can still be simplified without any
   delegation, since it always does one deterministic thing.
2. `tl` is currently documented and coded as *temporary*
   (`sourceme/aliases.source:9-14`, `README.md:98,117-119`: "Interim `tl`
   helper (temporary, feature-frozen)", with a retirement criterion). The
   decision is now to keep it permanently as a dependency-free fallback —
   that framing needs to flip everywhere it appears.
3. Live-testing the trust-gated sourcing prompt against a synthetic legacy
   project surfaced that the legacy-admin activation guidance
   (`src/taurworks/project_resolution.py:1908-1918`, "...was not sourced...")
   prints unconditionally, even on activations where Tier-1 trust-gated
   sourcing is enabled and the script is about to be (or already was)
   sourced moments later in the same output.
4. `taurworks project init --local` was attempted twice live and failed
   both times with `unrecognized arguments: --local` — `init`'s
   description (`src/taurworks/cli.py:663-671`) explains it operates on an
   existing/current directory but never states that `--local`/`--path` are
   `create`-only.

## Scope
- Simplify `tl`'s calling convention.
- Reframe `tl` in code and README as permanent, not temporary.
- Write one unified `tl`/`tw`/`taurworks` explanation in the README.
- Fix the `init` `--local` discoverability gap.
- Fix the stale legacy-admin guidance message.

## Required Changes
1. `sourceme/aliases.source`: change the argument check from requiring
   `tl activate NAME` to accepting `tl NAME` directly. Update the usage
   message and the header comment: drop "temporary"/retirement-criterion
   language, state the permanent break-glass framing instead. Do not change
   the lookup order or sourcing mechanics.
2. `README.md`: rewrite the `## Interim `tl` helper (temporary,
   feature-frozen)` section (`README.md:98-119`) into one unified
   explanation covering `taurworks` (read-only Python CLI), `tw` (sourced,
   config-aware activation layer), and `tl` (permanent, dependency-free,
   intentionally dumb break-glass fallback) — what each is for and the
   updated `tl NAME` syntax. Include the stale-shell-helper mitigation
   ("re-source `~/.config/taurworks/taurworks-shell.sh` after every
   taurworks update, the same way you'd re-source `.bashrc`") with a
   one-line forward pointer that a proper fix is being designed separately.
3. `src/taurworks/cli.py`: add an explicit line to `project init`'s
   `description=` (`cli.py:663-671`) stating that `--local`/`--path` are
   `create`-only and do not apply to `init`.
4. `src/taurworks/project_resolution.py`: make the legacy-admin "was not
   sourced" guidance (`project_resolution.py:1908-1918`) conditional so it
   does not claim sourcing didn't happen on an activation where Tier-1
   trust-gated sourcing is enabled and this activation sources (or sourced)
   the script. Exact conditional shape is the implementor's call.
5. Add tests: `tl` currently has zero automated coverage (its own work item,
   WI-INTERIM-TL-PIPX-0001, validated it manually only) — add shell-level
   tests for the new `tl NAME` syntax, and a test for the corrected
   legacy-admin guidance message under the Tier-1-enabled,
   about-to-source condition.

## Non-Goals
- Do not add delegation from `tl` to `tw` (checking whether `tw` exists,
  calling `tw activate`, etc.) — considered and explicitly rejected for the
  reasons in Problem/Context.
- Do not implement the `tw install`/`refresh` stale-shell-helper fix itself
  — that is being designed as its own separate work item; this item only
  documents the interim mitigation and cross-references the future fix.
- Do not add `--local` or any new flag to `project init` — the fix here is
  documentation only, since `init` genuinely has no ambiguity for `--local`
  to resolve.
- Do not touch `project/design/README.md`'s stale "Current design
  priorities" bullets — a separate small finding, not part of this scope.

## Acceptance Criteria
- `tl LCATS` (no `activate` verb) sources the project's setup script
  exactly as `tl activate LCATS` did before.
- The README's `tl`/`tw`/`taurworks` section is one coherent explanation,
  not two disconnected sections, and no longer states or implies `tl` will
  be deleted.
- `taurworks project init --local` (or `--help` on `init`) surfaces why
  `--local` doesn't apply, without requiring the user to already know
  `create`'s flags.
- Activating a legacy-admin project whose script is trust-gated-sourced
  this activation does not print guidance claiming it "was not sourced."
- `scripts/test` passes; `lrh validate` introduces no new errors (known
  pre-existing `contributors.md` errors excepted).

## Validation
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- Manual shell test: `tl LCATS` (real project) activates correctly after
  the syntax change

## Risk Notes
- Changing `tl`'s calling convention is a breaking change to its own
  contract, even with a blast radius of exactly one user for about a week
  — worth stating plainly rather than treating as a pure addition.
- The guidance-message fix touches code already reviewed twice this session
  (PR #69's guidance strings, PR #70's trust-gating) — should get the same
  test-coverage discipline those got, not be treated as a trivial wording
  tweak.
