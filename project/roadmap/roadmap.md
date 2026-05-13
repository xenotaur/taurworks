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
- First working-directory command slice: `project working-dir show` and `project working-dir set [DIR]`.
- Follow-on `project create PROJECT --working-dir DIR` integration that reuses refresh/scaffold logic.
- Follow-on `project activate --print` guidance based on configured `working_dir`.

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

## Phase 2B — Integrate working-directory metadata into project commands
- Add `project create PROJECT --working-dir DIR` metadata writing without duplicating refresh logic.
- Make `project activate --print` use configured `working_dir` for safe, inspectable guidance.
- Keep actual shell mutation for a later wrapper/function design.

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
