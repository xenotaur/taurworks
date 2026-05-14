# Current Status

## Maturity snapshot
Taurworks is in a design-alignment phase moving from successful `tw activate` dogfooding toward shell UX polish, project-list status classification, a minimal read-only `dev` scaffold, and activation-extension design while preserving current activation behavior.

## Current direction (documented)
- One primary executable: `taurworks`.
- Namespaced workspace lifecycle commands: `taurworks project ...`.
- Namespaced repo workflow commands: `taurworks dev ...`.
- Shared discovery/configuration core across namespaces.
- Compatibility coverage for existing top-level commands (`create`, `refresh`, `activate`, `projects`).
- Explicit separation between read-only activation guidance and shell-mutating `tw activate`.

## Implemented minimal project slice
- `taurworks project --help` documents the project namespace and available discovery commands.
- `taurworks project where` provides read-only project/config/discovery diagnostics.
- `taurworks project list` provides read-only discovery listing and clear no-project behavior.
- `taurworks project refresh`, `taurworks project create`, and `taurworks project activate --print` provide safe scaffolding and inspectable guidance, but dogfooding showed they need configured working-directory metadata before shell activation can be useful.

## What this phase prioritizes
- Making default `tw activate` output concise while preserving successful activation behavior.
- Moving detailed activation diagnostics behind `--verbose` or `--debug`.
- Adding `tw help` as an alias for `tw --help`.
- Classifying `tw projects` / `taurworks projects` output as initialized, workspace-only, or legacy-admin.
- Keeping activation limited to initialized projects with `.taurworks/config.toml` for now.
- Adding a minimal read-only `taurworks dev ...` scaffold with safe diagnostics before workflow automation.
- Designing activation extensions for readiness messages, environment strategies, trusted startup hooks, and legacy migration.

## What remains future implementation work
- Implementing the documented `tw` UX polish.
- Implementing project-list status classification.
- Implementing a minimal read-only `taurworks dev ...` scaffold.
- Designing and later implementing activation extensions in separate slices.
- Automatic legacy `Admin/project-setup.source` migration tooling.
- Multi-repo project management.
- Finalized migration/deprecation mechanics for compatibility commands.
- Expanded diagnostics and dry-run support across all command paths.

Automatic sourcing of legacy `Admin/project-setup.source` scripts is intentionally deferred because it crosses a stronger trust boundary than `cd`-only activation.
