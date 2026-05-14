# Unified Command Model

## Status note
The command model below is current design direction and roadmap intent. The shipped CLI now includes minimal `taurworks project ...` discovery/scaffold commands, existing-root initialization, working-directory metadata, read-only `project activate --print` guidance, and an explicit `tw activate` shell helper. Dogfooding showed the next design-aligned phase is shell UX polish, project-list status classification, a minimal read-only `dev` namespace scaffold, and activation-extension design before broader workflow automation or stronger trust behavior.

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
The current phase follows successful dogfooding of `tw activate` with a configured working directory. It is intentionally not broad repo workflow automation, not automatic legacy setup sourcing, and not multi-repo project management.

1. Polish the `tw` shell UX: concise default `tw activate` output, detailed diagnostics only with `--verbose` or `--debug`, concise default warnings for missing projects or working directories, `tw help` as an alias for `tw --help`, and no change to successful activation semantics.
2. Classify project-list entries for `tw projects` / `taurworks projects` as initialized projects with `.taurworks/config.toml`, workspace-only directories, or legacy-admin directories with `Admin/project-setup.source`.
3. Keep activation limited to initialized projects for now. Legacy-admin fallback sourcing must not become default behavior; a future migration script may handle old `Admin/project-setup.source` projects.
4. Add a minimal read-only `taurworks dev ...` scaffold, preferring safe diagnostics such as `dev where` and/or `dev status` before any `dev test`/automation expansion.
5. Design activation extensions for readiness messages, Conda/venv/Docker-style environment strategies, trusted per-project startup hooks, and legacy setup migration without implementing those behaviors in the polish slice.

## Compatibility and migration notes
- Existing top-level commands (`create`, `refresh`, `activate`, `projects`) are retained as compatibility commands.
- The `project` namespace now implements `where` and `list` as read-only commands. `list` currently supports conservative local metadata discovery and reports its limitations.
- Migration to namespaced forms should be incremental and documented.
- Deprecation planning should only begin after namespaced behavior is stable and compatibility coverage is verified.
- Breaking removals/renames are out of scope for the current documentation-alignment phase.

## Safety and shell-integration constraints
- Taurworks should not implicitly modify user shell startup files.
- `taurworks project activate --print` remains read-only activation guidance.
- `tw activate` is the explicit shell-mutating wrapper for `cd`-only activation.
- Legacy `Admin/project-setup.source` support is a migration/design topic, not an automatic fallback.
- Automatic sourcing of legacy setup scripts is intentionally deferred because it crosses a stronger trust boundary than `cd`-only activation.
- Documentation should distinguish instruction-printing commands from state-changing commands.
- Higher-risk state-changing commands should prefer conservative defaults and inspectable behavior.
