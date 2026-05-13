# Unified Command Model

## Status note
The command model below is current design direction and roadmap intent. The shipped CLI now includes minimal `taurworks project ...` discovery/scaffold commands and read-only `project activate --print` guidance, but the next design-aligned phase is working-directory metadata rather than full shell activation or full `taurworks dev ...` implementation.

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

## Next project implementation sequence
The next phase is the minimal metadata model needed to distinguish the Taurworks project root from the default activation/work target. It is intentionally not more package-layout work, not full `taurworks dev ...`, not automatic shell mutation, and not multi-repo project management.

1. Add `taurworks project working-dir show` and `taurworks project working-dir set [DIR]` as the first implementation slice for reading and writing `paths.working_dir` in `.taurworks/config.toml`.
2. Extend `taurworks project create PROJECT --working-dir DIR` so creation writes working-directory metadata while reusing the existing refresh/scaffold path instead of duplicating refresh logic.
3. Update `taurworks project activate --print` so it uses the configured `working_dir` to print safe, inspectable activation guidance for the intended work directory.
4. Leave actual parent-shell mutation through `tw activate`, shell functions, or wrappers for a later explicitly designed slice.

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
