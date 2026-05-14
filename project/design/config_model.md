# Configuration and State Model

## Precedence order
For developer workflow behavior (for example `taurworks dev ...` command resolution), configuration should resolve in this order (highest to lowest):

1. Command-line options
2. Repo-local workflow configuration (`taurdev.toml`)
3. Optional Python integration (`[tool.taurdev]` in `pyproject.toml`)
4. Visible project/workspace metadata (`.taurworks/`)
5. XDG-style global user configuration/state/cache
6. Built-in defaults

This precedence keeps repository-defined dev behavior authoritative while still allowing user defaults when repository config is absent.

## Global model (user scope)
Use XDG-style directories for user-level settings and registries, including workspace/project registration and user defaults.

## Project/workspace metadata (filesystem-visible)
Keep project/workspace operational metadata visible and inspectable under `.taurworks/`.

## Project-root and working-directory metadata
A Taurworks project needs two distinct path concepts before activation can become useful:

- `project_root` is the directory containing `.taurworks/`. It is the owner of Taurworks-visible project metadata.
- `working_dir` is the default code/work directory for day-to-day development. It is stored relative to `project_root` so project metadata remains portable across machines and checkout locations.

Dogfooding showed that the previous command slice can create, refresh, discover, and print activation guidance, but it still treats the project root as the effective work target. Legacy projects often used an `Admin/` directory for setup guidance beside a local repository; Taurworks should instead place owned metadata in `.taurworks/` and point to the intended repository or work tree through `working_dir`.

Minimal `.taurworks/config.toml` schema:

```toml
schema_version = 1

[project]
name = "ExampleProject"

[paths]
working_dir = "repo-or-work-dir"
```

Accepted path and command rules for the dogfood-resolution slice:

- `paths.working_dir` should be relative by default and interpreted from `project_root`.
- Absolute `working_dir` values should be rejected or deferred until an explicit design covers them.
- Empty project names in existing configs are legacy/underspecified metadata and are repaired to the project-root directory name when the config can be safely parsed and updated.
- `taurworks project init [PATH] [--working-dir DIR] [--create-working-dir]` initializes the existing/current project root safely and idempotently, reusing refresh/config logic.
- `taurworks project create NAME [--working-dir DIR] [--create-working-dir] [--nested]` creates a new project root, then delegates to init/refresh logic. It refuses accidental nested same-name creation when the current project/directory name already equals `NAME` unless `--nested` is supplied.
- `taurworks project working-dir show [PATH_OR_NAME]` displays the configured relative `paths.working_dir` or a clear unconfigured message for the selected project.
- `taurworks project working-dir set DIR --project PATH_OR_NAME` is the preferred mutation shape because it avoids ambiguous positional overloads. A no-target form may continue to mean the current project.
- `taurworks project create NAME --working-dir repo --create-working-dir` and `taurworks project working-dir set repo --create` are the explicit opt-ins for creating a missing working directory. Missing work directories should not be created silently.
- `taurworks project activate [PATH_OR_NAME] --print` reads configured `paths.working_dir`, validates that it is relative and resolves inside `project_root`, prints the absolute target path and a manual `cd` guidance command, uses the shared target resolver, and still performs no shell mutation.


Shared target resolution should be centralized across `project init`, `project create`, `project working-dir show/set`, and `project activate --print`. It should report diagnostics such as `input`, selected `project_root`, and `resolved_by` so dogfood failures like resolving `TestProject` from inside `TestProject` to `TestProject/TestProject` are visible and preventable.

## Repo-local workflow configuration
Use `taurdev.toml` as the primary repo-local workflow configuration surface.

Optional Python projects may also provide `[tool.taurdev]` in `pyproject.toml` when that integration is preferred.

The `taurdev` naming is intentional: it identifies repository-local developer workflow orchestration settings used by `taurworks dev ...` commands.

## Why standalone `taurdev.toml` matters
A standalone `taurdev.toml` is necessary because:

- Non-Python repositories may not have `pyproject.toml`.
- Some Python projects prefer not to place developer workflow metadata in `pyproject.toml`.
- Multi-repo workspaces may need separate workflow configuration per repository.

## Design intent
This model keeps global state standardized, project/workspace state inspectable, and repo workflow behavior explicit while preserving sensible defaults.
