# Design Overview

## Status note
The `taurworks project ...` and `taurworks dev ...` namespaces described below are the target design direction and are not yet fully implemented. The current project command slice can create/refresh visible metadata, discover projects, and print read-only activation guidance; dogfooding showed that the `project_root` / `working_dir` model is useful, but the command semantics need refinement before shell activation can be useful: existing-directory initialization must be separated from new-root creation, target resolution must be centralized, working-directory creation must be explicit, and accidental nested same-name projects must be guarded.

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
- `taurworks project working-dir show [PATH_OR_NAME]`
- `taurworks project working-dir set DIR --project PATH_OR_NAME`
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
Dogfooding the current `taurworks project ...` command family showed that this sequence should be completed before adding any shell wrapper that mutates the user shell:

1. Add `taurworks project init [PATH] [--working-dir DIR] [--create-working-dir]` for safe, idempotent initialization of an existing/current project root. It should reuse the same refresh/config logic instead of growing a competing scaffold path.
2. Refine `taurworks project create NAME [--working-dir DIR] [--create-working-dir] [--nested]` so it means creating a new project root directory and then delegating initialization to init/refresh. It should refuse accidental nested same-name creation when the current project or current directory already has the requested name unless `--nested` is supplied.
3. Centralize shared project target resolution across lifecycle commands and include diagnostic output describing the input, selected `project_root`, and `resolved_by` reason.
4. Extend `taurworks project working-dir show [PATH_OR_NAME]` to accept an optional target, and prefer `taurworks project working-dir set DIR --project PATH_OR_NAME` over ambiguous positional overloads.
5. Require explicit opt-in before creating a missing working directory: `project create NAME --working-dir repo --create-working-dir` or `project working-dir set repo --create`.
6. Keep `taurworks project activate [PATH_OR_NAME] --print` read-only while making it use the shared resolver and configured `working_dir`.

Automatic shell mutation through `tw activate` or another shell wrapper remains a later slice. Full `taurworks dev ...` behavior and multi-repo project management are also deferred.

## Compatibility commands
Existing top-level commands such as `create`, `refresh`, `activate`, and `projects` remain documented compatibility commands until a migration plan is finalized.

## Project init, create, and target-resolution design
`project init` and `project create` should have distinct meanings:

- `taurworks project init [PATH] [--working-dir DIR] [--create-working-dir]` initializes an existing/current directory as a Taurworks project root. It is safe and idempotent, should not imply a new parent/child directory, and should reuse refresh/config logic for `.taurworks/` scaffolding and metadata repair.
- `taurworks project create NAME [--working-dir DIR] [--create-working-dir] [--nested]` creates a new project root directory, then delegates to init/refresh. If the current project name or current directory basename already equals `NAME`, `create` should refuse to create `NAME/NAME` unless the user supplies `--nested`.

Shared target resolution should be centralized and diagnostic:

1. No input resolves the current project if one is present; otherwise the command may apply its own documented default.
2. Existing filesystem paths resolve as paths.
3. Input equal to the current project name resolves to the current project root.
4. Input equal to the current working-directory basename, when the current directory is or should be the target, resolves to the current directory for init-like behavior.
5. Otherwise, input is treated as a child path relative to the current working directory.

Diagnostic output should make the resolver decision inspectable, for example:

```text
- input: TestProject
- project_root: /path/to/TestProject
- resolved_by: current_project_name
```

Working-directory commands should use the same resolver. `taurworks project working-dir show [PATH_OR_NAME]` should accept an optional target. For mutation, prefer `taurworks project working-dir set DIR --project PATH_OR_NAME` rather than adding ambiguous positional overloads.

Missing working directories should only be created with explicit opt-in. Accepted forms are `taurworks project create NAME --working-dir repo --create-working-dir` and `taurworks project working-dir set repo --create`. Without the opt-in, commands may record or validate metadata according to their command contract, but must not silently create a code/work directory.

`taurworks project activate [PATH_OR_NAME] --print` remains read-only: it should use the shared resolver, print diagnostics and guidance, and avoid shell mutation. `tw activate` and any actual parent-shell mutation remain future work after the dogfood-resolution sequence above lands.

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
