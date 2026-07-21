---
resolution: null
blocked_reason: null
blocked: false
id: WI-SHELL-HELPER-REFRESH-0001
title: Add `tw shell refresh` to fix on-demand shell-helper staleness
type: deliverable
status: proposed
owner: null
contributors: []
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/shell_helper_refresh.md
  - project/design/activation_extension.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - run_tests
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - implement_passive_staleness_detection
acceptance:
  - "tw shell refresh regenerates the on-disk helper file from the currently installed package and re-sources it into the invoking shell, verified by a real dogfood shell test"
  - "tw shell refresh fails clearly and leaves the on-disk file unmodified when taurworks shell print fails"
  - "TAURWORKS_SHELL_HELPER_PATH override is respected when set; the documented default (~/.config/taurworks/taurworks-shell.sh) is used otherwise"
  - "README.md documents tw shell refresh next to the existing tw activate shell-helper section, and the pre-existing Stale shell-helper mitigation note no longer references the tw install/tw refresh placeholder"
  - "scripts/test passes; lrh validate introduces no new errors"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/taurworks/resources/shell/taurworks-shell.sh
  - README.md
  - test files exercising the new shell function (path determined by existing shell-integration test conventions)
---

# WI-SHELL-HELPER-REFRESH-0001: Add `tw shell refresh` to fix on-demand shell-helper staleness

## Summary
Add `tw shell refresh`, an explicit shell function (sibling to `tw activate`)
that regenerates the on-disk `taurworks-shell.sh` helper from the currently
installed package and re-sources it into the current shell, closing the
on-demand half of the stale-shell-helper gap.

## Problem / Context
`taurworks shell print > ~/.config/taurworks/taurworks-shell.sh` followed by
`source` is a one-time snapshot: it never auto-updates when the `taurworks`
package changes, and any already-open shell keeps running whatever version
it last sourced, silently, with no error. This bit real usage repeatedly
during 2026-07-11 through 2026-07-18 dogfooding — guidance-string and
trust-gated-sourcing behavior from two merged PRs were silently missing from
an already-sourced `tw` for most of a session. `project/design/
shell_helper_refresh.md` designs the fix in two phases: Option A
(`tw shell refresh`, on-demand, no CLI payload changes) and Option B (a
passive hash-mismatch warning piggybacked on `tw activate`, deferred until
Option A has been dogfooded). This work item implements Option A only.

## Scope
- Add a new `tw shell refresh` shell function to
  `src/taurworks/resources/shell/taurworks-shell.sh`, dispatched by `tw()`
  alongside `activate`/`help`.
- Document the command and the `TAURWORKS_SHELL_HELPER_PATH` override in
  `README.md` next to the existing `tw activate` shell-helper section, and
  update the existing "Stale shell-helper mitigation" note (currently
  around `README.md:139-152`) to name the real command instead of its
  current placeholder text.
- No changes to `taurworks shell print`, `project_resolution.py`, or
  activation semantics.

## Required Changes
1. In `src/taurworks/resources/shell/taurworks-shell.sh`, add a
   `_tw_shell_refresh()` function that:
   - resolves the target path via
     `${TAURWORKS_SHELL_HELPER_PATH:-$HOME/.config/taurworks/taurworks-shell.sh}`;
   - runs `command taurworks shell print` and, on success, writes the result
     to the resolved path (creating the parent directory if needed), then
     `source` it;
   - reports a clear error and returns non-zero without touching the file if
     `taurworks shell print` fails;
   - prints a one-line confirmation naming the refreshed path.
2. Add `shell refresh` dispatch to `tw()` in the same file, following the
   existing `activate`/`help` special-case pattern (`tw shell refresh`
   intercepted before falling through to plain `command taurworks "$@"`
   delegation).
3. Update `README.md`'s "`tw activate` shell helper" section (currently
   starting around `README.md:699` — confirm the current line at
   implementation time, since this repo's README has shifted before) to
   document `tw shell refresh` and the `TAURWORKS_SHELL_HELPER_PATH`
   override.
4. Update the existing "Stale shell-helper mitigation" note in `README.md`
   (currently around `README.md:139-152`, added by `WI-TL-BREAKGLASS-0001`)
   to name `tw shell refresh` as the actual implemented command, replacing
   the current `tw install`/`tw refresh` placeholder text.
5. Add shell-integration tests exercising `tw shell refresh`, mirroring
   however existing `_tw_activate` shell-function tests are structured,
   covering: successful refresh, `taurworks shell print` failure leaves the
   existing file untouched, and the `TAURWORKS_SHELL_HELPER_PATH` override.

## Non-Goals
- Do not implement passive staleness detection or any hash/version marker
  consumed by `tw activate` (Option B in `project/design/
  shell_helper_refresh.md`) — deferred to a follow-up work item, opened only
  after this item has been dogfooded.
- Do not change `taurworks shell print`'s output contract, add fields to the
  `--shell` activation payload, or touch `project_resolution.py`.
- Do not add any automatic regeneration trigger to `scripts/develop`,
  `pipx install`, or `pipx upgrade` (Option D in the design, rejected as a
  primary mechanism).
- Do not attempt to reach or refresh any shell other than the one in which
  `tw shell refresh` is invoked — that remains an unavoidable limit of the
  subprocess/parent-shell boundary, not something this item can close.
- Do not add hand-edit detection or preservation for the generated helper
  file — it remains fully generated and disposable by documented convention;
  `tw shell refresh` overwrites it unconditionally.
- Do not update the stale "Current design priorities" bullet list in
  `project/design/README.md` — flagged separately in the design doc, not
  required for this item.

## Acceptance Criteria
- `tw shell refresh` regenerates the on-disk helper file from the currently
  installed package and re-sources it into the invoking shell, verified by a
  real dogfood shell test (edit the packaged resource, `tw shell refresh`,
  confirm new behavior is live without opening a new shell).
- `tw shell refresh` fails clearly and leaves the on-disk file unmodified
  when `taurworks shell print` fails (e.g. resource missing).
- `TAURWORKS_SHELL_HELPER_PATH` override is respected when set, and the
  documented default (`~/.config/taurworks/taurworks-shell.sh`) is used
  otherwise.
- `README.md` documents `tw shell refresh` next to the existing
  `tw activate` helper section, and the pre-existing "Stale shell-helper
  mitigation" note no longer references the `tw install`/`tw refresh`
  placeholder.
- `scripts/test` passes; `lrh validate` introduces no new errors.

## Validation
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- Manual shell test: source the helper, edit the packaged resource (or
  reinstall an updated editable checkout), run `tw shell refresh`, confirm
  the new behavior is live in the same shell without restarting it.

## Related Workstream and Designs
- Design: `project/design/shell_helper_refresh.md`
- Related design: `project/design/activation_extension.md` (same
  safety-boundary precedent: `tw activate` as the explicit shell-mutating
  sibling of a read-only command)

## Risk Notes
- `TAURWORKS_SHELL_HELPER_PATH` resolution must stay consistent between
  wherever the user is documented to have installed the file and what
  `tw shell refresh` targets, or refresh will silently write to the wrong
  location while the shell keeps sourcing the stale one.
- Writing the regenerated file should not leave a truncated/partial file on
  disk if `taurworks shell print` fails partway or the write is
  interrupted; prefer a safe write pattern (e.g. write-then-move) over an
  in-place overwrite.
