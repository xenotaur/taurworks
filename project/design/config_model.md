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
