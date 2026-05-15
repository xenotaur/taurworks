# Design Overview

## Status note
The `taurworks project ...` and `taurworks dev ...` namespaces described below are the target design direction and are not yet fully implemented. The current project command slice can create/refresh visible metadata, discover nearby projects, initialize existing roots, record working-directory metadata, and print read-only activation guidance. Dogfooding has now shown that Taurworks needs global resolution before richer activation: an XDG-style user config, explicit workspace root, and global project registry should let `tw projects` and `tw activate` resolve projects from anywhere without recursive scanning or automatic legacy script sourcing.

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
Dogfooding confirmed that local initialized-project activation works, but also exposed the global resolution gap: a project created in a nested working directory may be valid locally while remaining undiscoverable from the workspace root unless it is registered. The accepted direction is to find projects reliably first, then activate them richly.

The next sequence is design-first and should not implement behavior changes in the control-plane alignment PR:

1. **Phase 1a — XDG global config and workspace root:** use `$XDG_CONFIG_HOME/taurworks/config.toml`, falling back to `~/.config/taurworks/config.toml`, with schema version 1 and explicit `[workspace].root`. Planned commands are `taurworks config where`, `taurworks workspace show`, and `taurworks workspace set PATH`. `~/Workspace` may be inferred only as a non-mutating convenience when it already exists and no config exists; explicit configuration is required before persisting or treating it as authoritative.
2. **Phase 1b — Global project registry:** support `[projects.NAME].root` entries in global config and planned commands `taurworks project register NAME PATH`, `taurworks project unregister NAME`, and `taurworks project registry list`. Registered projects cover intentionally weird or nested locations without recursive scanning by default.
3. **Phase 1c — Workspace/registry-aware listing and activation:** make `tw projects` / `taurworks projects` merge registered projects, immediate workspace-root children, initialized projects, legacy-admin projects, and workspace-only projects. Make `tw activate NAME` resolve from anywhere by stable priority: registered project, initialized workspace project, legacy-admin workspace project, workspace-only directory, local/enclosing fallback, then child path only for explicitly local commands.
4. **Phase 2 — Declarative activation config:** design and then implement `.taurworks/config.toml` activation data for readiness messages, environment strategies, and exports without arbitrary user-script sourcing.
5. **Future phase — Safe user-script support:** support scripts/hooks only behind explicit opt-in with warnings, inspection/dry-run modes, per-project trust, and no default automatic legacy setup sourcing.

The safety boundary for this sequence is:

```text
taurworks project activate --print
  read-only activation guidance

tw activate
  explicit shell-mutating function from sourced taurworks-shell.sh

workspace-only / legacy-admin fallback
  cd only, with warning

legacy Admin/project-setup.source
  recognized for migration/design, not automatic sourcing

user scripts/hooks
  future explicit opt-in only
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

`taurworks project activate [PATH_OR_NAME] --print` remains read-only: it should use the shared resolver, print diagnostics and guidance, and avoid shell mutation. `tw activate`, when provided by the sourced `taurworks-shell.sh` function, is the explicit shell-mutating layer for changing directory only; future activation-extension work should be designed before adding environment activation or project-script execution.

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
