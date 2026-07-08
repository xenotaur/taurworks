---
id: ROADMAP-INIT
title: Unified Taurworks Direction Roadmap
status: active
confidence: medium
---

# Roadmap

## Horizon framing

This roadmap is phased and conservative. It prioritizes command-model alignment, safe incremental delivery, and explicit trust boundaries.

## Current phase snapshot (2026-07-06)

Phases 1 through 2D below are implemented and merged. The active phase is the
remainder of Phase 5 (legacy inspect/migrate) plus the side-effect audit
follow-ups; Phase 5A (trusted hooks) and Phase 6/7 remain future work.

### In scope now

- `taurworks legacy inspect`/`legacy migrate` design and implementation for `Admin/project-setup.source` projects.
- Side-effect audit follow-ups (`project/audits/side_effects.md`), especially gating legacy Conda environment creation behind an explicit command/flag.
- Deciding scope for `taurworks dev ...` workflow automation beyond read-only diagnostics.
- Future safe user-script support design behind explicit opt-in (Phase 5A), once legacy inspect/migrate is dogfooded.

### Out of scope now

- Implementing trusted hooks before legacy inspect/migrate is dogfooded.
- Automatic fallback sourcing of `Admin/project-setup.source`.
- Treating legacy-admin projects as anything more than `cd`-only warning fallbacks before explicit migration/trust design.
- Broad `taurworks dev ...` workflow automation without further design.
- Shell startup-file edits.
- Multi-repo project management.
- Breaking removals or renames of compatibility commands.
- Broad refactors unrelated to project metadata and shell UX alignment.

## Phase 1 — Document unified product direction (done)

- Align project artifacts around one executable: `taurworks`.
- Document `taurworks project ...` and `taurworks dev ...` responsibilities.
- Preserve current top-level commands as compatibility commands.

## Phase 2 — Formalize config/state model (done)

- Define precedence and config discovery behavior.
- Align XDG-style global config/state/cache with visible project-local metadata and repo-local workflow config.

## Phase 2A0 — Add XDG global config and workspace root (done)

- Use `$XDG_CONFIG_HOME/taurworks/config.toml`, falling back to `~/.config/taurworks/config.toml`.
- Store an explicit `[workspace].root` in schema version 1 global config.
- Implemented commands: `taurworks config where`, `taurworks workspace show`, and `taurworks workspace set PATH`.
- `~/Workspace` is inferred only as non-mutating first-run inference when it exists and no config exists; explicit configuration is required before persisting state or treating it as authoritative.

## Phase 2A1 — Add global project registry (done)

- Store explicit registered project roots under `[projects.NAME]` in global config.
- Implemented commands: `taurworks project register NAME PATH`, `taurworks project unregister NAME`, and `taurworks project registry list`.
- Support intentionally weird or nested project locations without recursive scanning by default.
- Report stale registry paths without silently deleting user intent.

## Phase 2A2 — Make listing and activation workspace/registry-aware (done)

- Merge registered projects, immediate workspace-root children, initialized projects, legacy-admin projects, and workspace-only projects in `tw projects` / `taurworks projects`.
- Resolve `tw activate NAME` from anywhere using the canonical priority in `project/design/config_model.md`: registered project, initialized workspace project, legacy-admin workspace project, workspace-only directory, local/enclosing fallback, then child path only for explicitly local commands.
- Script-friendly `tw project root PROJECT`, `tw project working PROJECT`, `tw root PROJECT`, and `tw working PROJECT` path emitters use the same resolution core; stdout remains path-only for shell composition.
- Fallback activation stays conservative: initialized projects with `working_dir` cd there; initialized without `working_dir`, workspace-only, and legacy-admin cd to project root with warnings; legacy scripts are not sourced by default.

## Phase 2A — Align project-root and working-directory metadata (done)

- `project_root` is the directory containing `.taurworks/`.
- `working_dir` is the default code/work directory, stored relative to `project_root` in `.taurworks/config.toml`.
- Absolute working-directory paths are rejected/deferred until explicitly designed.
- Empty project names in existing configs are treated as legacy metadata and repaired.
- `project working-dir show/set` shipped before activation behavior changed.

## Phase 2B — Resolve project init/create and working-directory dogfood findings (done)

- `project init [PATH] [--working-dir DIR] [--create-working-dir]` safely and idempotently initializes existing/current project roots.
- `project create NAME [--working-dir DIR] [--create-working-dir] [--nested]` creates a new project root, delegates to init/refresh, and refuses accidental nested same-name creation unless `--nested` is supplied.
- Target resolution is centralized for project lifecycle, working-directory, and read-only activation commands with diagnostics that show `input`, `project_root`, and `resolved_by`.
- `project working-dir show [PATH_OR_NAME]` is target-aware; `project working-dir set DIR --project PATH_OR_NAME` is the preferred mutation shape.
- `--create-working-dir` or `working-dir set --create` is required before creating missing working directories.
- `project activate --print` uses the shared resolver while remaining read-only.

## Phase 2C — Polish explicit shell activation (done)

- `taurworks project activate --print` remains read-only activation guidance.
- `tw activate` is shell-mutating only through the explicitly sourced `taurworks-shell.sh` function.
- Default `tw activate` output is concise; detailed diagnostics live behind `--verbose`/`--debug`.
- Missing project and missing working-directory failures stay concise by default.
- `tw help` is an alias for `tw --help`.

## Phase 2D — Classify project-list status (done)

- `tw projects` / `taurworks projects` distinguish initialized projects with `.taurworks/config.toml`, workspace-only directories, and legacy-admin directories with `Admin/project-setup.source`.
- Superseded by Phase 2A2 for activation targets: initialized projects remain the richest activation targets, while initialized-without-working-dir, workspace-only, and legacy-admin projects may be `cd`-only warning fallbacks.
- Legacy-admin fallback sourcing is not default behavior.
- Old `Admin/project-setup.source` scripts remain for a future explicit migration or trust flow (Phase 5/5A).

## Phase 3 — Introduce/document namespaced project lifecycle (done)

- `taurworks project` namespace covers lifecycle operations.
- Existing `create`, `refresh`, `activate`, and `projects` command behavior is preserved during transition.

## Phase 4 — Add minimal read-only `taurworks dev` scaffold (done)

- `taurworks dev ...` was introduced conservatively.
- Safe diagnostics: `dev where` and `dev status`.
- The scaffold remains read-only: it reports workspace context and future VCS automation boundaries without running workflow commands.
- `dev test`, `dev clean`, and other workflow automation remain deferred until trust boundaries are clear (see "In scope now").

## Phase 5 — Design and implement declarative activation (message/exports/Conda done; venv/Docker/hooks deferred)

- Readiness messages such as "Ready for work on project X" are implemented (`[activation].message`).
- `[activation.exports]` declarative environment data is implemented.
- Conda environment activation (`[activation.environment] type = "conda"`) is implemented in `tw activate`.
- venv, Docker/devcontainer, and other environment activation strategies remain deferred to separate designs.
- `taurworks legacy inspect PROJECT` and `taurworks legacy migrate PROJECT --apply` remain the active remaining work in this phase (see `WI-ACTIVATION-CONFIG-0001`).
- Arbitrary user-script sourcing remains out of scope for this phase.

## Phase 5A — Future safe user-script support (not started)

- Design trusted per-project startup hooks with explicit opt-in and disablement semantics.
- Require warnings, inspection/dry-run modes, and per-project trust before executing hooks.
- Preserve no default automatic legacy `Admin/project-setup.source` sourcing.
- Design migration for legacy setup scripts into declarative config plus explicitly trusted hooks where necessary.
- Start only after Phase 5's legacy inspect/migrate tooling has been dogfooded.

## Phase 6 — Defer higher-risk dev commands until stable (not started)

- Defer `sandbox`, `precommit`, `publish`, `version`, `validate`, and `update` until core behavior and guardrails are proven.

## Phase 7 — Define compatibility migration path (not started)

- After compatibility is preserved and namespaced commands are stable, define deprecation/migration for legacy top-level commands.

## Untracked follow-up: side-effect audit recommendations

The 2026-05-17 post-merge side-effect audit (`project/audits/side_effects.md`)
produced seven follow-up recommendations that are not yet captured as a
tracked phase or work item, most notably that legacy top-level `taurworks
refresh`/`taurworks create` (and therefore `tw refresh`/`tw create`) still
create a Conda environment by default despite sounding like safe metadata
operations. See the proposed work item created alongside this roadmap update
for the full list.
