# Current Status

## Maturity snapshot
Taurworks is in a design-alignment phase moving from basic project scaffolding/discovery toward a minimal metadata model that separates `project_root`, `working_dir`, and activation target while preserving current behavior.

## Current direction (documented)
- One primary executable: `taurworks`.
- Namespaced workspace lifecycle commands: `taurworks project ...`.
- Namespaced repo workflow commands: `taurworks dev ...`.
- Shared discovery/configuration core across namespaces.
- Compatibility coverage for existing top-level commands (`create`, `refresh`, `activate`, `projects`).

## Implemented minimal project slice
- `taurworks project --help` documents the project namespace and available discovery commands.
- `taurworks project where` provides read-only project/config/discovery diagnostics.
- `taurworks project list` provides read-only discovery listing and clear no-project behavior.
- `taurworks project refresh`, `create`, and `activate --print` provide safe scaffolding and inspectable guidance, but dogfooding showed they need configured working-directory metadata before shell activation can be useful.

## What this phase prioritizes
- Aligning design/control-plane docs around `.taurworks/config.toml` project metadata.
- Defining `project_root` as the directory containing `.taurworks/` and `working_dir` as a relative path from that root.
- Sequencing `project working-dir show/set`, then `project create --working-dir`, then `project activate --print` integration.

## What remains future implementation work
- Full command implementation across all `taurworks dev` verbs.
- Automatic shell mutation through aliases, wrappers, or shell functions.
- Multi-repo project management.
- Finalized migration/deprecation mechanics for compatibility commands.
- Expanded diagnostics and dry-run support across all command paths.
