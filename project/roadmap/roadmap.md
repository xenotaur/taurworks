---
id: ROADMAP-INIT
title: Unified Taurworks Direction Roadmap
status: active
confidence: medium
---

# Roadmap

## Horizon framing

This roadmap is phased and conservative. It prioritizes command-model alignment, safe incremental delivery, and explicit trust boundaries.

## Current phase snapshot (2026-05-14)

### In scope now

- Post-dogfood sourced `taurworks-shell.sh` `tw activate` UX polish.
- Concise default activation output with verbose/debug diagnostics gated behind explicit flags.
- `tw help` as an alias for `tw --help`.
- Project-list status classification for initialized, workspace-only, and legacy-admin directories.
- A minimal read-only `taurworks dev ...` namespace scaffold.
- Activation-extension design for readiness messages, environment activation strategies, trusted startup hooks, and legacy setup migration.

### Out of scope now

- Changing successful sourced `taurworks-shell.sh` `tw activate` behavior.
- Automatic fallback sourcing of `Admin/project-setup.source`.
- Treating legacy-admin projects as activation targets before migration.
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
- Prefer safe diagnostics such as `dev where` and/or `dev status`.
- Defer `dev test`, `dev clean`, and other workflow automation until the scaffold and trust boundaries are clear.

## Phase 5 — Design activation extensions before implementation

- Design readiness messages such as “Ready for work on project X”.
- Design Conda, venv, Docker/devcontainer, and other environment activation strategies.
- Design trusted per-project startup hooks with explicit trust and disablement semantics.
- Design migration for legacy `Admin/project-setup.source` projects.
- Document trust/safety boundaries for sourcing project scripts before any implementation.

## Phase 6 — Defer higher-risk dev commands until stable

- Defer `sandbox`, `precommit`, `publish`, `version`, `validate`, and `update` until core behavior and guardrails are proven.

## Phase 7 — Define compatibility migration path

- After compatibility is preserved and namespaced commands are stable, define deprecation/migration for legacy top-level commands.
