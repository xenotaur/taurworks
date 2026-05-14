# Design Overview

## Status note
The `taurworks project ...` and `taurworks dev ...` namespaces described below are the target design direction and are not yet fully implemented. The current project command slice can create/refresh visible metadata, discover projects, initialize existing roots, record working-directory metadata, and print read-only activation guidance. Dogfooding has now shown that the explicit `tw activate` shell helper can safely change into the configured working directory, so the next sequence is UX polish, project-list classification, a minimal read-only `dev` namespace scaffold, and activation-extension design without adding stronger shell trust behavior yet.

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
Dogfooding confirmed this activation path works for the first validation workflow:

```bash
tw project create TestProject --working-dir test_repo --create-working-dir
tw activate TestProject
```

The wrapper changes into the configured working directory, and missing project activation fails safely. The next implementation sequence should therefore polish the current behavior without changing the core activation semantics:

1. **`tw` UX polish:** make default `tw activate` output concise, move detailed activation diagnostics behind `--verbose` or `--debug`, keep missing project/working-directory failures as concise warnings by default, add `tw help` as an alias for `tw --help`, and preserve the current successful activation behavior.
2. **Project-list status classification:** make `tw projects` / `taurworks projects` distinguish initialized projects with `.taurworks/config.toml`, workspace-only directories, and legacy-admin directories with `Admin/project-setup.source`. Activation should continue to support initialized projects only for now.
3. **Minimal `dev` namespace scaffold:** add a read-only `taurworks dev ...` namespace with safe diagnostics such as `dev where` and/or `dev status`; do not add broad repo workflow automation in this slice.
4. **Activation-extension design:** design, but do not implement, readiness messages, environment activation strategies, trusted per-project startup hooks, and legacy `Admin/project-setup.source` migration.

The safety boundary for this sequence is:

```text
taurworks project activate --print
  read-only activation guidance

tw activate
  explicit shell-mutating wrapper

legacy Admin/project-setup.source
  migration/design topic, not automatic fallback
```

Automatic sourcing of legacy `Admin/project-setup.source` scripts is intentionally deferred because it crosses a stronger trust boundary than `cd`-only activation. Full repo workflow automation and multi-repo management remain deferred.

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

`taurworks project activate [PATH_OR_NAME] --print` remains read-only: it should use the shared resolver, print diagnostics and guidance, and avoid shell mutation. `tw activate` is the explicit shell-mutating wrapper for changing directory only; future activation-extension work should be designed before adding environment activation or project-script execution.

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
