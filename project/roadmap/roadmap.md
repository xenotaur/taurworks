---
id: ROADMAP-INIT
title: Unified Taurworks Direction Roadmap
status: active
confidence: medium
---

# Roadmap

## Horizon framing
This roadmap is phased and conservative. It prioritizes command-model alignment and safe incremental delivery.

## Current phase snapshot (2026-05-13)

### In scope now
- Minimal project metadata model distinguishing `project_root`, relative `working_dir`, and activation target.
- `.taurworks/config.toml` schema alignment for `schema_version`, `[project].name`, and `[paths].working_dir`.
- Dogfood-resolution design for distinct `project init` and `project create` semantics.
- Central shared target resolution with inspectable diagnostics (`input`, `project_root`, and `resolved_by`).
- Target-aware working-directory commands, explicit working-directory creation opt-ins, and nested same-name project guardrails.
- Read-only `project activate --print` guidance based on configured `working_dir` and the shared resolver.

### Out of scope now
- More package-layout work as the primary next phase.
- Full `taurworks dev ...` implementation.
- Automatic shell mutation or `tw activate` wrapper behavior.
- Multi-repo project management.
- Breaking removals or renames of compatibility commands.
- Broad refactors unrelated to project metadata alignment.

## Phase 1 — Document unified product direction
- Align project artifacts around one executable: `taurworks`.
- Document `taurworks project ...` and `taurworks dev ...` responsibilities.
- Preserve current top-level commands as compatibility commands.

## Phase 2 — Formalize config/state model
- Define precedence and config discovery behavior.
- Align XDG-style global config/state/cache with visible project-local metadata and repo-local workflow config.

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
- Complete this dogfood-resolution sequence before adding actual shell mutation through `tw activate` or a wrapper/function.

## Phase 3 — Introduce/document namespaced project lifecycle
- Introduce or document `taurworks project` namespace for lifecycle operations.
- Preserve existing `create`, `refresh`, `activate`, and `projects` command behavior during transition.

## Phase 4 — Deliver minimal `taurworks dev` MVP
- Focus on `init`, `test`, `lint`, `format`, `coverage`, `clean`, and `develop`.
- Keep command resolution transparent and inspectable.

## Phase 5 — Defer higher-risk dev commands until stable
- Defer `sandbox`, `precommit`, `publish`, `version`, `validate`, and `update` until core behavior and guardrails are proven.

## Phase 6 — Define compatibility migration path
- After compatibility is preserved and namespaced commands are stable, define deprecation/migration for legacy top-level commands.
