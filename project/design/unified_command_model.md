# Unified Command Model

## Status note
The command model below is implemented for the scope described here. The shipped CLI includes `taurworks project ...` discovery/scaffold commands, existing-root initialization, working-directory metadata, read-only `project activate --print` guidance, an explicitly sourced `taurworks-shell.sh` `tw activate` shell helper, XDG-style global config and workspace-root commands, a global project registry, workspace/registry-aware project listing and activation resolution, a minimal read-only `taurworks dev ...` scaffold (`dev where`, `dev status`), and declarative activation (`[activation].message`, `[activation.exports]`, Conda environment activation). Remaining work is legacy `Admin/project-setup.source` inspect/migrate tooling, trusted user-script hooks, and broader `dev` workflow automation beyond read-only diagnostics.

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

Optional user-local aliases may be documented for non-mutating shorthand:

```bash
alias td='taurworks dev'
```

Do not document `alias tw=taurworks` as equivalent to the sourceable `taurworks-shell.sh` helper. An alias cannot change the parent shell directory, while the sourced `tw` function can implement `tw activate` as explicit `cd`-only shell mutation. These aliases and helpers are opt-in and user-controlled.

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

## Remaining implementation sequence
Shell UX polish, project-list status classification, the read-only `dev` scaffold, and the first declarative-activation slices (message, exports, Conda) are implemented. It is intentionally still not broad repo workflow automation, not automatic legacy setup sourcing, and not multi-repo project management. Remaining work:

1. Add `taurworks legacy inspect PROJECT` and `taurworks legacy migrate PROJECT --apply` to help migrate `Admin/project-setup.source` projects to declarative config without executing those scripts (see `WI-ACTIVATION-CONFIG-0001`).
2. Design and implement trusted per-project startup hooks only after legacy inspect/migrate has been dogfooded, with explicit opt-in, warnings, and content-change detection.
3. Expand `taurworks dev ...` beyond read-only diagnostics (`dev where`, `dev status`) into workflow automation, once trust boundaries for that expansion are designed.
4. Address the outstanding side-effect audit follow-ups (`project/audits/side_effects.md`), notably that legacy top-level `taurworks refresh`/`create` still create a Conda environment by default despite sounding like safe metadata operations.

## Compatibility and migration notes
- Existing top-level commands (`create`, `refresh`, `activate`, `projects`) are retained as compatibility commands.
- The `project` namespace implements `where` and `list` as read-only commands. `list` merges registered, workspace, initialized, legacy-admin, and workspace-only projects per `config_model.md`.
- Migration to namespaced forms should be incremental and documented.
- Deprecation planning should only begin after namespaced behavior is stable and compatibility coverage is verified.
- Breaking removals/renames are out of scope for the current documentation-alignment phase.

## Safety and shell-integration constraints
- Taurworks should not implicitly modify user shell startup files.
- `taurworks project activate --print` remains read-only activation guidance.
- `tw activate` is shell-mutating only when provided by the sourced `taurworks-shell.sh` function; a plain alias to `taurworks` cannot change the parent shell.
- Legacy `Admin/project-setup.source` support is a migration/design topic, not an automatic fallback.
- Automatic sourcing of legacy setup scripts is intentionally deferred because it crosses a stronger trust boundary than `cd`-only activation.
- Documentation should distinguish instruction-printing commands from state-changing commands.
- Higher-risk state-changing commands should prefer conservative defaults and inspectable behavior.
