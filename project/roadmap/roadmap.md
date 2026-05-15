---
id: ROADMAP-INIT
title: Unified Taurworks Direction Roadmap
status: active
confidence: medium
---

# Roadmap

## Horizon framing

This roadmap is phased and conservative. It prioritizes command-model alignment, safe incremental delivery, and explicit trust boundaries.

## Current phase snapshot (2026-05-15)

### In scope now

- XDG-style global config and explicit workspace root design.
- Global project registry design for intentionally nested or unusual project locations.
- Workspace/registry-aware `tw projects` and `tw activate` resolution design.
- Conservative activation fallback semantics for initialized, workspace-only, legacy-admin, and registered projects.
- Declarative activation config design for readiness messages, environment strategies, and exports.
- Future safe user-script support design behind explicit opt-in.

### Out of scope now

- Implementing global config, registry commands, or activation behavior in this design-alignment PR.
- Changing successful sourced `taurworks-shell.sh` `tw activate` behavior.
- Automatic fallback sourcing of `Admin/project-setup.source`.
- Treating legacy-admin projects as anything more than `cd`-only warning fallbacks before explicit migration/trust design.
- Broad `taurworks dev ...` workflow automation.
- Shell startup-file edits.
- Multi-repo project management.
- Breaking removals or renames of compatibility commands.
- Broad refactors unrelated to project metadata and shell UX alignment.

## Phase 1 — Document unified product direction

- Align project artifacts around one executable: `taurworks`.
- Document `taurworks project ...` and `taurworks dev ...` responsibilities.
- Preserve current top-level commands as compatibility commands.

## Phase 2 — Formalize config/state model

- Define precedence and config discovery behavior.
- Align XDG-style global config/state/cache with visible project-local metadata and repo-local workflow config.

## Phase 2A0 — Add XDG global config and workspace root

- Use `$XDG_CONFIG_HOME/taurworks/config.toml`, falling back to `~/.config/taurworks/config.toml`.
- Store an explicit `[workspace].root` in schema version 1 global config.
- Add planned commands: `taurworks config where`, `taurworks workspace show`, and `taurworks workspace set PATH`.
- Allow `~/Workspace` only as non-mutating first-run inference when it exists and no config exists; require explicit configuration before persisting state or treating it as authoritative.

## Phase 2A1 — Add global project registry

- Store explicit registered project roots under `[projects.NAME]` in global config.
- Add planned commands: `taurworks project register NAME PATH`, `taurworks project unregister NAME`, and `taurworks project registry list`.
- Support intentionally weird or nested project locations without recursive scanning by default.
- Report stale registry paths without silently deleting user intent.

## Phase 2A2 — Make listing and activation workspace/registry-aware

- Merge registered projects, immediate workspace-root children, initialized projects, legacy-admin projects, and workspace-only projects in `tw projects` / `taurworks projects`.
- Resolve `tw activate NAME` from anywhere using stable priority: registered project, initialized workspace project, legacy-admin workspace project, workspace-only directory, local/enclosing fallback, then child path only for explicitly local commands.
- Keep fallback activation conservative: initialized projects with `working_dir` cd there; initialized without `working_dir`, workspace-only, and legacy-admin cd to project root with warnings; legacy scripts are not sourced by default.

## Phase 2A — Align project-root and working-directory metadata

- Define `project_root` as the directory containing `.taurworks/`.
- Define `working_dir` as the default code/work directory, stored relative to `project_root` in `.taurworks/config.toml`.
- Treat absolute working-directory paths as rejected/deferred until explicitly designed.
- Treat empty project names in existing configs as legacy metadata to repair in future implementation work.
- Implement `project working-dir show/set` before changing create or activation behavior.

## Phase 2B — Resolve project init/create and working-directory dogfood findings

- Add `project init [PATH] [--working-dir DIR] [--create-working-dir]` for safe, idempotent initialization of existing/current project roots.
- Refine `project create NAME [--working-dir DIR] [--create-working-dir] [--nested]` so it creates a new project root, delegates to init/refresh, and refuses accidental nested same-name creation unless `--nested` is supplied.
- Centralize target resolution for project lifecycle, working-directory, and read-only activation commands with diagnostics that show `input`, `project_root`, and `resolved_by`.
- Make `project working-dir show [PATH_OR_NAME]` target-aware and prefer `project working-dir set DIR --project PATH_OR_NAME` for mutation.
- Require `--create-working-dir` or `working-dir set --create` before creating missing working directories.
- Make `project activate --print` use the shared resolver while remaining read-only.
- Complete this sequence before relying on shell mutation.

## Phase 2C — Polish explicit shell activation

- Keep `taurworks project activate --print` as read-only activation guidance.
- Keep `tw activate` shell-mutating only through the explicitly sourced `taurworks-shell.sh` function.
- Make default `tw activate` output concise.
- Move detailed activation diagnostics behind `--verbose` or `--debug`.
- Keep missing project and missing working-directory failures concise by default.
- Add `tw help` as an alias for `tw --help`.

## Phase 2D — Classify project-list status

- Make `tw projects` / `taurworks projects` distinguish initialized projects with `.taurworks/config.toml`, workspace-only directories, and legacy-admin directories with `Admin/project-setup.source`.
- Keep activation support limited to initialized projects for now.
- Do not add legacy-admin fallback sourcing as default behavior.
- Leave old `Admin/project-setup.source` projects for a future explicit migration script.

## Phase 3 — Introduce/document namespaced project lifecycle

- Introduce or document `taurworks project` namespace for lifecycle operations.
- Preserve existing `create`, `refresh`, `activate`, and `projects` command behavior during transition.

## Phase 4 — Add minimal read-only `taurworks dev` scaffold

- Introduce `taurworks dev ...` conservatively.
- Provide safe diagnostics such as `dev where` and `dev status`.
- Keep the scaffold read-only: report workspace context and future VCS automation boundaries without running workflow commands.
- Defer `dev test`, `dev clean`, and other workflow automation until the scaffold and trust boundaries are clear.

## Phase 5 — Design declarative activation before implementation

- Design readiness messages such as “Ready for work on project X”.
- Design Conda, venv, Docker/devcontainer, and other environment activation strategies.
- Design `[activation.exports]` as declarative environment data, not shell code.
- Avoid arbitrary user-script sourcing in the declarative activation phase.
- Document trust/safety boundaries for sourcing project scripts before any implementation.

## Phase 5A — Future safe user-script support

- Design trusted per-project startup hooks with explicit opt-in and disablement semantics.
- Require warnings, inspection/dry-run modes, and per-project trust before executing hooks.
- Preserve no default automatic legacy `Admin/project-setup.source` sourcing.
- Design migration for legacy setup scripts into declarative config plus explicitly trusted hooks where necessary.

## Phase 6 — Defer higher-risk dev commands until stable

- Defer `sandbox`, `precommit`, `publish`, `version`, `validate`, and `update` until core behavior and guardrails are proven.

## Phase 7 — Define compatibility migration path

- After compatibility is preserved and namespaced commands are stable, define deprecation/migration for legacy top-level commands.
