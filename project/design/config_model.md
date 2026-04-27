# Configuration and State Model

## Precedence order
Configuration should resolve in this order (highest to lowest):

1. Command-line options
2. XDG-style global user configuration/state/cache
3. Visible project/workspace metadata (`Admin/` or `.taurworks/`)
4. Repo-local workflow configuration (`taurdev.toml`)
5. Optional Python integration (`[tool.taurdev]` in `pyproject.toml`)
6. Built-in defaults

## Global model (user scope)
Use XDG-style directories for user-level settings and registries, including workspace/project registration and user defaults.

## Project/workspace metadata (filesystem-visible)
Keep project/workspace operational metadata visible and inspectable under a project admin path such as `Admin/` or `.taurworks/`.

## Repo-local workflow configuration
Use `taurdev.toml` as the primary repo-local workflow configuration surface.

Optional Python projects may also provide `[tool.taurdev]` in `pyproject.toml` when that integration is preferred.

## Why standalone `taurdev.toml` matters
A standalone `taurdev.toml` is necessary because:

- Non-Python repositories may not have `pyproject.toml`.
- Some Python projects prefer not to place developer workflow metadata in `pyproject.toml`.
- Multi-repo workspaces may need separate workflow configuration per repository.

## Design intent
This model keeps global state standardized, project/workspace state inspectable, and repo workflow behavior explicit while preserving sensible defaults.
