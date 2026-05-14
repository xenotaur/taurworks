# Unified Command Model

## Status note
The command model below is current design direction and roadmap intent. The shipped CLI now includes minimal `taurworks project ...` discovery/scaffold commands and read-only `project activate --print` guidance. Dogfooding showed the next design-aligned phase is refining `project init` versus `project create`, centralizing target resolution, and making working-directory creation explicit before full shell activation or full `taurworks dev ...` implementation.

## Why one primary executable: `taurworks`
A single primary executable keeps command discovery simple, avoids duplicated initialization paths, and reduces user confusion around which binary owns workspace vs development behavior.

## Why separate `project` and `dev` namespaces
Taurworks separates responsibilities while sharing core internals:

- `taurworks project ...` handles workspace lifecycle, registration, activation, environment setup, listing, and project metadata.
- `taurworks dev ...` orchestrates repo-local developer workflows by delegating to project scripts and standard tools.

This separation keeps workflow semantics clear without requiring independent tools.

## Shared config and discovery model
Both namespaces should rely on shared configuration/discovery services (path normalization, config loading, diagnostics, and precedence handling) so behavior is consistent and inspectable.

See `project/design/config_model.md` for precedence and repository-vs-global resolution details.

## Why short names are not installed by default
Short names like `tw`, `td`, and `dev` are not installed globally by default because they can collide with existing user commands, shell functions, or other toolchains.

Optional user-local aliases may be documented:

```bash
alias tw=taurworks
alias td='taurworks dev'
```

These aliases are opt-in and user-controlled.

## Command namespace intent (planned/target)

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

## Next project implementation sequence
The current phase addresses dogfood findings in the project lifecycle command family. It is intentionally not more package-layout work, not full `taurworks dev ...`, not automatic shell mutation, and not multi-repo project management.

1. Add `taurworks project init [PATH] [--working-dir DIR] [--create-working-dir]` for safe, idempotent initialization of an existing/current project root. Reuse refresh/config logic rather than creating a separate scaffold implementation.
2. Refine `taurworks project create NAME [--working-dir DIR] [--create-working-dir] [--nested]` so create means new root creation followed by init/refresh delegation. Guard against accidental `NAME/NAME` nested creation when the current project or directory already has the requested name unless `--nested` is supplied.
3. Centralize shared target resolution so no input, existing paths, current project-name input, current-directory basename input, and child-path fallback behave consistently across project commands.
4. Emit resolver diagnostics such as `input`, `project_root`, and `resolved_by` so command output explains why a target was selected.
5. Extend `taurworks project working-dir show [PATH_OR_NAME]` and prefer `taurworks project working-dir set DIR --project PATH_OR_NAME` for target-aware working-directory metadata.
6. Require explicit opt-in before creating a missing working directory: `project create NAME --working-dir repo --create-working-dir` or `project working-dir set repo --create`.
7. Keep `taurworks project activate [PATH_OR_NAME] --print` read-only while making it use the shared resolver and configured `working_dir` metadata.
8. Leave actual parent-shell mutation through `tw activate`, shell functions, or wrappers for a later explicitly designed slice after this dogfood-resolution sequence is complete.

## Compatibility and migration notes
- Existing top-level commands (`create`, `refresh`, `activate`, `projects`) are retained as compatibility commands.
- The `project` namespace now implements `where` and `list` as read-only commands. `list` currently supports conservative local metadata discovery and reports its limitations.
- Migration to namespaced forms should be incremental and documented.
- Deprecation planning should only begin after namespaced behavior is stable and compatibility coverage is verified.
- Breaking removals/renames are out of scope for the current documentation-alignment phase.

## Safety and shell-integration constraints
- Taurworks should not implicitly modify user shell startup files.
- Activation flows should print explicit operator instructions when parent-shell state must change.
- Documentation should distinguish instruction-printing commands from state-changing commands.
- Higher-risk state-changing commands should prefer conservative defaults and inspectable behavior.
