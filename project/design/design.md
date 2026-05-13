# Design Overview

## Status note
The `taurworks project ...` and `taurworks dev ...` namespaces described below are the target design direction and are not yet fully implemented. The current project command slice can create/refresh visible metadata, discover projects, and print read-only activation guidance; dogfooding showed the next design need is to separate `project_root` from `working_dir` before shell activation can be useful.

## Product model
Taurworks uses one executable, `taurworks`, with two namespaces:

- `taurworks project ...` for workspace/project lifecycle and activation concerns.
- `taurworks dev ...` for repo-local development workflow orchestration.

These namespaces are conceptually separate, but should share core services for discovery, configuration loading, diagnostics, and path normalization.

## Project root vs working directory
`project_root` is the directory containing `.taurworks/`; it owns Taurworks metadata such as `.taurworks/config.toml`. `working_dir` is the default code/work directory used for day-to-day development and activation guidance. It should be stored in `.taurworks/config.toml` relative to `project_root` for portability.

The minimal planned schema is:

```toml
schema_version = 1

[project]
name = "ExampleProject"

[paths]
working_dir = "repo-or-work-dir"
```

Absolute working-directory paths are deferred unless a later design explicitly accepts them, and empty legacy project names should be repaired by future implementation work.

## CLI namespace model

### Project namespace
- `taurworks project init`
- `taurworks project create`
- `taurworks project refresh`
- `taurworks project where`
- `taurworks project working-dir show`
- `taurworks project working-dir set [DIR]`
- `taurworks project activate --print`
- `taurworks project list`

### Dev namespace
- `taurworks dev init`
- `taurworks dev clean`
- `taurworks dev develop`
- `taurworks dev test`
- `taurworks dev smoke`
- `taurworks dev coverage`
- `taurworks dev lint`
- `taurworks dev format`
- `taurworks dev build`
- `taurworks dev update`
- `taurworks dev precommit`
- `taurworks dev publish`
- `taurworks dev sandbox`
- `taurworks dev version`
- `taurworks dev validate`

## Immediate design-aligned implementation sequence
1. Implement `taurworks project working-dir show` and `taurworks project working-dir set [DIR]` for the config schema above.
2. Extend `taurworks project create PROJECT --working-dir DIR` to write working-directory metadata while delegating shared scaffolding to refresh logic.
3. Extend `taurworks project activate --print` to use configured `working_dir` when printing safe, inspectable activation guidance.

Automatic shell mutation through `tw activate` or another shell wrapper remains a later slice. Full `taurworks dev ...` behavior and multi-repo project management are also deferred.

## Compatibility commands
Existing top-level commands such as `create`, `refresh`, `activate`, and `projects` remain documented compatibility commands until a migration plan is finalized.

## Dev command resolution model
For `taurworks dev <command>`, resolution should follow this order:

1. Explicit configured command
2. Project-local script (for example `scripts/test`)
3. Built-in default selected from project type/layout

This model preserves project intent while providing a reliable fallback path.

## Transparency and safety
- Command behavior should be explainable and inspectable.
- Dry-run, verbose, and doctor-style diagnostics should be supported where practical.
- Higher-risk commands (`clean`, `precommit`, `publish`, `update`, `sandbox`) should use conservative defaults and avoid implicit destructive behavior.

## Non-goals
- Do not replace standard tools with a new build/lint/test/package/release system.
- Do not split into unrelated init/discovery flows for project vs dev operations.
