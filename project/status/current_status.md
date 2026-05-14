# Current Status

## Maturity snapshot
Taurworks is in a design-alignment phase moving from basic project scaffolding/discovery and the initial `project_root` / `working_dir` metadata model toward refined project lifecycle semantics that resolve dogfood findings while preserving current behavior.

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
- `taurworks project refresh`, `taurworks project create`, and `taurworks project activate --print` provide safe scaffolding and inspectable guidance, but dogfooding showed they need configured working-directory metadata before shell activation can be useful.

## What this phase prioritizes
- Aligning design/control-plane docs around `.taurworks/config.toml` project metadata.
- Defining `project_root` as the directory containing `.taurworks/` and `working_dir` as a relative path from that root.
- Distinguishing `project init` for existing/current roots from `project create` for new project roots.
- Centralizing target resolution with diagnostics that show `input`, selected `project_root`, and `resolved_by`.
- Making `working-dir show` target-aware, preferring `working-dir set DIR --project PATH_OR_NAME`, and requiring explicit opt-in before creating missing working directories.
- Preventing accidental nested same-name projects unless `--nested` is supplied.
- Completing this dogfood-resolution sequence before adding `tw activate` or shell-wrapper mutation.

## What remains future implementation work
- Implementing the documented `project init`, resolver, `project create`, `working-dir`, and `activate --print` refinements.
- Full command implementation across all `taurworks dev` verbs.
- Automatic shell mutation through aliases, wrappers, or shell functions.
- Multi-repo project management.
- Finalized migration/deprecation mechanics for compatibility commands.
- Expanded diagnostics and dry-run support across all command paths.
