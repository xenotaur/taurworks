# Unified Command Model

## Why one primary executable: `taurworks`
A single primary executable keeps command discovery simple, avoids duplicated initialization paths, and reduces user confusion around which binary owns workspace vs development behavior.

## Why separate `project` and `dev` namespaces
Taurworks separates responsibilities while sharing core internals:

- `taurworks project ...` handles workspace lifecycle, registration, activation, environment setup, listing, and project metadata.
- `taurworks dev ...` orchestrates repo-local developer workflows by delegating to project scripts and standard tools.

This separation keeps workflow semantics clear without requiring independent tools.

## Why short names are not installed by default
Short names like `tw`, `td`, and `dev` are not installed globally by default because they can collide with existing user commands, shell functions, or other toolchains.

Optional user-local aliases may be documented:

```bash
alias tw=taurworks
alias td='taurworks dev'
```

These aliases are opt-in and user-controlled.

## Expected project commands
- `taurworks project init`
- `taurworks project activate`
- `taurworks project list`
- `taurworks project refresh`

## Expected dev commands
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

## Compatibility and migration notes
- Existing top-level commands (`create`, `refresh`, `activate`, `projects`) are retained as compatibility commands.
- Migration to namespaced forms should be incremental and documented.
- Deprecation planning should only begin after namespaced behavior is stable and compatibility coverage is verified.
