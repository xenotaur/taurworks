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
  - "`taurworks setup` places the packaged `tl` source file at a documented, stable location and prints the exact `source` lines for both files to add to the shell startup file, without editing any startup file itself; `sourceme/`'s file(s) are added to `setup.py`'s `package_data` as part of this work item (idempotent no-op if `WI-BIN-REPO-SPLIT-0001` already added the same entry), and placement is validated against an installed wheel/pipx environment, not only with `PYTHONPATH=src`"
  - "`tw shell refresh` (`src/taurworks/resources/shell/taurworks-shell.sh`) resolves its target path with the same `TAURWORKS_SHELL_HELPER_PATH` → `XDG_CONFIG_HOME` → `~/.config` precedence `taurworks setup` uses, so a refresh after an XDG-based setup updates and re-sources the same file every new shell loads — not a stale `$HOME/.config` copy"
  - "new `scripts/install` shim derives the repository root (matching the pattern in `scripts/build`/`scripts/check-workflows`) and runs `pipx install . --force && taurworks setup` from that root, so invoking the shim by absolute path or from another working directory still installs the correct checkout; documented in README.md as the from-git-checkout entry point"
  - "tests cover `taurworks setup`'s idempotent re-run behavior, its XDG_CONFIG_HOME/TAURWORKS_SHELL_HELPER_PATH resolution logic, and an integration sequence of setup (XDG path) followed by `tw shell refresh`, confirming both target the same file"
  - "README.md's install section documents the new one-step flow, superseding the old multi-step manual `pipx install` + `taurworks shell print` + ad-hoc `tl` copy sequence"
artifacts_expected:
  - src/taurworks/cli.py
  - src/taurworks/setup.py (or equivalent new module)
  - src/taurworks/resources/shell/taurworks-shell.sh
  - setup.py
  - sourceme/
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

Review found two real cross-WI/existing-code gaps that this work item must
account for, not defer past:

- **Refresh/setup path drift.** `tw shell refresh` (existing code,
  `src/taurworks/resources/shell/taurworks-shell.sh:349`) always targets
  `${TAURWORKS_SHELL_HELPER_PATH:-$HOME/.config/taurworks/taurworks-shell.sh}`
  — no `XDG_CONFIG_HOME` awareness. If `taurworks setup` installs to an
  XDG-resolved path while `refresh` keeps targeting the plain `~/.config`
  path, a refresh after setup would update and re-source a *different*
  file than every new shell loads. This work item therefore includes a
  matching XDG-aware path-resolution fix in `tw shell refresh` itself — a
  narrow, path-resolution-only exception to the broader Non-Goal below of
  not touching `tw shell refresh`'s regenerate/re-source behavior.
- **`tl` packaging dependency.** This work item's `taurworks setup` needs
  to place a packaged `tl` source file, but `setup.py`'s `package_data`
  currently only lists `resources/shell/taurworks-shell.sh`.
  `WI-BIN-REPO-SPLIT-0001` also lists wiring `sourceme/` into
  `package_data` among its own acceptance criteria, but this work item does
  not treat that as a soft prerequisite it can leave undone — this work
  item's Required Changes and `artifacts_expected` (below) include adding
  `sourceme/`'s file(s) to `setup.py`'s `package_data` directly, so
  `taurworks setup`'s `tl`-placement acceptance criterion is met
  regardless of merge order relative to `WI-BIN-REPO-SPLIT-0001`. If that
  work item's change has already landed by the time this one is
  implemented, adding the same `package_data` entry here is an idempotent
  no-op, not a conflict. `taurworks setup`'s `tl` placement must be
  validated against an actual installed wheel/pipx environment, not only
  `PYTHONPATH=src`, which would not catch a missing `package_data` entry.
  (Not recorded as a formal `depends_on` in this WI's frontmatter:
  `WI-BIN-REPO-SPLIT-0001` isn't merged yet, and `lrh validate`'s
  `UNKNOWN_DEPENDENCY` check rejects a `depends_on` reference to a WI ID
  not yet present in the tree — this work item owning the change directly
  makes that sequencing question moot rather than needing to be tracked.)

## Scope

- New `taurworks setup` subcommand, modeled on the existing `tw shell
  refresh` regenerate-and-report shape.
- Matching XDG-aware path resolution in `tw shell refresh`.
- New `scripts/install` shim for the from-checkout entry point.
- README.md updates documenting the new one-step install flow.

## Required Changes

1. Add `taurworks setup` to `src/taurworks/cli.py`'s argparse wiring,
   delegating to a new formatter/implementation module.
2. Implement XDG-aware shell-helper path resolution: prefer
   `$TAURWORKS_SHELL_HELPER_PATH`, then `$XDG_CONFIG_HOME/taurworks/taurworks-shell.sh`
   when valid, then `~/.config/taurworks/taurworks-shell.sh`.
3. Apply the same resolution precedence to `_tw_shell_refresh`'s
   `target_path` computation in
   `src/taurworks/resources/shell/taurworks-shell.sh`, so `tw shell
   refresh` updates and re-sources the same file `taurworks setup` wrote.
4. Add `sourceme/`'s file(s) to `setup.py`'s `package_data` (idempotent
   no-op if `WI-BIN-REPO-SPLIT-0001` already added the same entry), then
   place the packaged `tl` source file at a documented, stable location
   under the same config directory. Validate placement from an installed
   wheel/pipx environment, not only `PYTHONPATH=src`.
5. Print the exact `source` lines for both files; never write to
   `.bashrc`/`.zshrc`/`.profile` directly.
6. Report a truth-first summary of what was created/updated/unchanged,
   matching the convention `project refresh`/`project init` already use.
7. Add `scripts/install`: derive the repository root the same way
   `scripts/build`/`scripts/check-workflows` do
   (`repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)`, then `cd
   "$repo_root"`) before running `pipx install . --force && taurworks
   setup`, so invoking the shim by absolute path or from another working
   directory still installs the correct checkout.
8. Update README.md's install section.

## Non-Goals

- The `bin/`/`taurscripts` repo split itself (separate WI,
  `WI-BIN-REPO-SPLIT-0001`) — this WI only depends on its `sourceme/`
  packaging output, it does not redo that work.
- The Conda PATH-loss diagnostic in `tw` (separate WI).
- The `--debug`/`TAURWORKS_DEBUG` flag and narration audit (separate WI).
- Any change to `tw activate`/`tw shell refresh`'s activation or
  regenerate/re-source *behavior* — the only in-scope change to `tw shell
  refresh` is matching its target-path *resolution* to `taurworks setup`'s,
  per the gap noted above.
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
  add to the shell startup file, without editing any startup file itself;
  `sourceme/`'s file(s) are added to `setup.py`'s `package_data` as part
  of this work item (idempotent no-op if `WI-BIN-REPO-SPLIT-0001` already
  added the same entry), and placement is validated against an installed
  wheel/pipx environment, not only with `PYTHONPATH=src`.
- `tw shell refresh` resolves its target path with the same
  `TAURWORKS_SHELL_HELPER_PATH` → `XDG_CONFIG_HOME` → `~/.config`
  precedence `taurworks setup` uses, so a refresh after an XDG-based setup
  updates and re-sources the same file every new shell loads.
- New `scripts/install` shim derives the repository root (matching
  `scripts/build`/`scripts/check-workflows`'s pattern) and runs `pipx
  install . --force && taurworks setup` from that root, and is documented
  in README.md as the from-git-checkout entry point.
- Tests cover `taurworks setup`'s idempotent re-run behavior, its
  `XDG_CONFIG_HOME`/`TAURWORKS_SHELL_HELPER_PATH` resolution logic, and an
  integration sequence of setup (XDG path) followed by `tw shell refresh`,
  confirming both target the same file.
- README.md's install section documents the new one-step flow, superseding
  the old multi-step manual `pipx install` + `taurworks shell print` +
  ad-hoc `tl` copy sequence.

## Validation

- ./scripts/format --check --diff
- ./scripts/lint
- ./scripts/test
- taurworks setup (manual dogfood check against a scratch `$HOME`, including with `$XDG_CONFIG_HOME` set)
- tw shell refresh after an XDG-based setup, confirming it targets the same file
- scripts/install from an absolute path and from a directory other than the repo root
- pip/pipx install of the built package, confirming the tl source file is present and placeable
- lrh validate
