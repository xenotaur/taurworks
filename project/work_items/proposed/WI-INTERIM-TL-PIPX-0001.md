---
id: WI-INTERIM-TL-PIPX-0001
title: Interim tl activation helper, pipx install path, and retirement criterion
type: deliverable
status: proposed
blocked: false
blocked_reason: null
resolution: null
---

# WI-INTERIM-TL-PIPX-0001: Interim tl helper, pipx install path, and retirement criterion

## Summary
Provide an immediately usable interim activation path (`tl`, a feature-frozen
shell function that sources legacy setup scripts) and a conda-independent
install path (`pipx install --editable`), with an explicit written criterion
for retiring `tl`.

## Problem / Context
The 2026-07-11 dogfood session found that daily work is blocked in two ways:
`tw activate` cannot yet activate Conda environments for real projects, and
the `taurworks` command disappears whenever the active Conda environment
changes because it is only installed in the `Taurworks` env. This pressure has
repeatedly derailed development toward circling. Decoupling "today works" from
"taurworks is finished" removes that pressure. `sourceme/aliases.source`
already contains a previous-generation `tw()` helper that silently collides
with the `tw()` from `taurworks shell print` (whichever is sourced last wins);
it is 80% of the needed `tl` and 100% of the cautionary tale. A plain
`pip install` of this package into a bare venv was verified working in the
dogfood session (stdlib-only runtime deps, working console_scripts entry).

## Scope
- Rename/repair `sourceme/aliases.source` into a feature-frozen `tl` helper.
- Document the pipx-based install as the supported way to get `taurworks` on
  PATH across Conda environments.
- Record the `tl` retirement criterion in writing.

## Required Changes
1. In `sourceme/aliases.source`, rename the `tw()` function to `tl()`,
   removing the name collision with the generated `taurworks-shell.sh`
   helper. Look up `$TAURWORKS_WORKSPACE/<NAME>/Admin/project-setup.source`
   first, then `.taurworks/project-setup.source`; source whichever exists,
   error otherwise.
2. Audit `sourceme/completions.source`: it must not advertise `tl` and should
   not break when both helpers are sourced.
3. Add a README section documenting
   `pipx install --editable ~/Workspace/Taurworks/taurworks` as the supported
   install path (with `scripts/develop` remaining the constrained dev-env
   path), including how it fixes the command-not-found-after-env-switch
   failure.
4. Record the retirement criterion in the README section and in this work
   item: `tl` is deleted (and `sourceme/aliases.source` removed) once every
   project the owner activates in a normal week works via `tw activate`.

## Non-Goals
- Do not add any feature to `tl` beyond lookup-and-source (no completions,
  listing, config, or flags). If `tl` needs a feature, fix `tw` instead.
- Do not publish taurworks to PyPI.
- Do not modify `src/taurworks/resources/shell/taurworks-shell.sh`.
- Do not delete `sourceme/aliases.source` yet — that is the retirement step.

## Acceptance Criteria
- Sourcing both `sourceme/aliases.source` and a generated
  `taurworks-shell.sh` in one shell leaves `tw` bound to the taurworks helper
  and `tl` bound to the interim helper.
- In a real shell, `tl activate LCATS` activates the LCATS Conda environment
  and changes directory (verified with `$CONDA_DEFAULT_ENV` and `pwd`).
- After `pipx install --editable`, `taurworks --help` works in a shell whose
  active Conda environment is not `Taurworks`.
- `lrh validate` introduces no new errors (known pre-existing
  `contributors.md` errors excepted).

## Validation
- `lrh validate`
- `scripts/lint`
- `bash -c 'source sourceme/aliases.source && source <(taurworks shell print) && type tl && type tw'`

## Risk Notes
- Interim helpers ossify; `sourceme/aliases.source` itself is the proof.
  The feature freeze and written retirement criterion are the mitigations.
- `tl` executes legacy scripts with no gating — identical in risk to the
  manual `source Admin/project-setup.source` the owner performs today; it
  adds lookup convenience, not new capability.
