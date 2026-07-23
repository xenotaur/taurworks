---
id: WI-TAURWORKS-SETUP-0001
title: Add `taurworks setup` command and `scripts/install` shim
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
  - implement_bin_repo_split
  - implement_path_loss_diagnostic
  - implement_debug_flag
  - edit_shell_startup_files
acceptance:
  - "`taurworks setup` subcommand exists, is idempotent, and writes the shell helper to `$XDG_CONFIG_HOME/taurworks/taurworks-shell.sh` when `XDG_CONFIG_HOME` is a valid absolute path, falling back to `~/.config/taurworks/taurworks-shell.sh` otherwise, honoring `$TAURWORKS_SHELL_HELPER_PATH` as the highest-precedence override"
  - "`taurworks setup` places the packaged `tl` source file at a documented, stable location and prints the exact `source` lines for both files to add to the shell startup file, without editing any startup file itself"
  - "new `scripts/install` shim runs `pipx install . --force && taurworks setup` (non-editable) and is documented in README.md as the from-git-checkout entry point"
  - "tests cover `taurworks setup`'s idempotent re-run behavior and its XDG_CONFIG_HOME/TAURWORKS_SHELL_HELPER_PATH resolution logic"
  - "README.md's install section documents the new one-step flow, superseding the old multi-step manual `pipx install` + `taurworks shell print` + ad-hoc `tl` copy sequence"
artifacts_expected:
  - src/taurworks/cli.py
  - src/taurworks/setup.py (or equivalent new module)
  - scripts/install
  - README.md
  - tests/
---

# WI-TAURWORKS-SETUP-0001: Add `taurworks setup` command and `scripts/install` shim

## Summary

Add a `taurworks setup` CLI subcommand that performs first-install/upgrade
wiring in one idempotent step — writing the shell helper to an XDG-aware
location, placing the `tl` source file, and printing the exact `source`
lines to add to the shell startup file — plus a `scripts/install` shim for
the from-git-checkout entry point. This is Decisions #1 from
`project/design/packaging_and_install.md`.

## Problem / Context

`tw` and `tl` are currently installed by two different, partly-undocumented
methods: `tw` via `taurworks shell print > ~/.config/taurworks/taurworks-shell.sh`
+ manual `source`, `tl` via copying `sourceme/aliases.source` to a
self-chosen location. There is no single documented or scripted path from
"fresh checkout" to "working `tw`/`tl`", and the shell-helper location does
not honor `$XDG_CONFIG_HOME` even though `global_config.py` already does for
Taurworks' own config file.

Prior art check: no existing `taurworks setup` or `scripts/install`
implementation found in-repo (`grep -rl "taurworks setup\|scripts/install"`
across work items/roadmap/focus returns nothing); no open work item or
backlog entry already requests this. `project/focus/current_focus.md`
(`FOCUS-CURRENT`) is scoped to legacy migration tooling, not packaging;
`project/roadmap/roadmap.md` has no phase covering install/packaging yet —
`related_focus`/`related_roadmap` are left empty, consistent with
`WI-SHELL-HELPER-REFRESH-0001`'s precedent.

This is one of four work items drafted from
`project/design/packaging_and_install.md`; the other three cover the
`bin/`/`taurscripts` repo split, the Conda PATH-loss diagnostic in `tw`,
and the `--debug`/`TAURWORKS_DEBUG` flag audit. This work item is scoped to
the setup/install command only.

## Scope

- New `taurworks setup` subcommand, modeled on the existing `tw shell
  refresh` regenerate-and-report shape.
- New `scripts/install` shim for the from-checkout entry point.
- README.md updates documenting the new one-step install flow.

## Required Changes

1. Add `taurworks setup` to `src/taurworks/cli.py`'s argparse wiring,
   delegating to a new formatter/implementation module.
2. Implement XDG-aware shell-helper path resolution: prefer
   `$TAURWORKS_SHELL_HELPER_PATH`, then `$XDG_CONFIG_HOME/taurworks/taurworks-shell.sh`
   when valid, then `~/.config/taurworks/taurworks-shell.sh`.
3. Place the packaged `tl` source file at a documented, stable location
   under the same config directory.
4. Print the exact `source` lines for both files; never write to
   `.bashrc`/`.zshrc`/`.profile` directly.
5. Report a truth-first summary of what was created/updated/unchanged,
   matching the convention `project refresh`/`project init` already use.
6. Add `scripts/install`: `pipx install . --force && taurworks setup`.
7. Update README.md's install section.

## Non-Goals

- The `bin/`/`taurscripts` repo split (separate WI).
- The Conda PATH-loss diagnostic in `tw` (separate WI).
- The `--debug`/`TAURWORKS_DEBUG` flag and narration audit (separate WI).
- Any change to `tw activate`/`tw shell refresh` semantics.
- PyPI publication.
- Automatically editing shell startup files.

## Acceptance Criteria

- `taurworks setup` subcommand exists, is idempotent, and writes the shell
  helper to `$XDG_CONFIG_HOME/taurworks/taurworks-shell.sh` when
  `XDG_CONFIG_HOME` is a valid absolute path, falling back to
  `~/.config/taurworks/taurworks-shell.sh` otherwise, honoring
  `$TAURWORKS_SHELL_HELPER_PATH` as the highest-precedence override.
- `taurworks setup` places the packaged `tl` source file at a documented,
  stable location and prints the exact `source` lines for both files to
  add to the shell startup file, without editing any startup file itself.
- New `scripts/install` shim runs `pipx install . --force && taurworks
  setup` (non-editable) and is documented in README.md as the
  from-git-checkout entry point.
- Tests cover `taurworks setup`'s idempotent re-run behavior and its
  `XDG_CONFIG_HOME`/`TAURWORKS_SHELL_HELPER_PATH` resolution logic.
- README.md's install section documents the new one-step flow, superseding
  the old multi-step manual `pipx install` + `taurworks shell print` +
  ad-hoc `tl` copy sequence.

## Validation

- ./scripts/format --check --diff
- ./scripts/lint
- ./scripts/test
- taurworks setup (manual dogfood check against a scratch `$HOME`)
- lrh validate
