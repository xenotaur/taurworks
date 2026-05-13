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

Current path rules for the working-directory metadata slice:

- `paths.working_dir` should be relative by default and interpreted from `project_root`.
- Absolute `working_dir` values should be rejected or deferred until an explicit design covers them.
- Empty project names in existing configs are legacy/underspecified metadata and are repaired to the project-root directory name when the config can be safely parsed and updated.
- `taurworks project working-dir show` displays the configured relative `paths.working_dir` or a clear unconfigured message.
- `taurworks project working-dir set [DIR]` stores an existing directory inside `project_root` as a relative path. If `DIR` is omitted, it uses the current directory relative to `project_root`.
- `taurworks project create PROJECT --working-dir DIR` ensures the project root exists, delegates Taurworks-owned scaffolding to `project refresh`, validates that `DIR` is relative and remains inside `project_root`, and records `paths.working_dir` as a relative path without creating that work directory.
- `taurworks project activate --print` still treats activation behavior as a later integration point; actual activation guidance has not yet been changed to use `working_dir`.

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
