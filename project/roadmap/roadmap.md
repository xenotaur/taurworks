---
id: ROADMAP-INIT
title: Unified Taurworks Direction Roadmap
status: active
confidence: medium
---

# Roadmap

## Horizon framing
This roadmap is phased and conservative. It prioritizes command-model alignment and safe incremental delivery.

## Current phase snapshot (2026-04-27)

### In scope now
- Documentation/design alignment around one primary executable (`taurworks`).
- Clear command responsibilities for `taurworks project ...` and `taurworks dev ...`.
- Shared configuration/discovery model clarity across both namespaces.
- Safety and shell-integration guardrails.
- Compatibility/migration-path documentation without breaking removals.

### Out of scope now
- Immediate implementation of every planned `taurworks dev` command.
- Breaking removals or renames of compatibility commands.
- Broad refactors unrelated to command-model alignment.

## Phase 1 — Document unified product direction
- Align project artifacts around one executable: `taurworks`.
- Document `taurworks project ...` and `taurworks dev ...` responsibilities.
- Preserve current top-level commands as compatibility commands.

## Phase 2 — Formalize config/state model
- Define precedence and config discovery behavior.
- Align XDG-style global config/state/cache with visible project-local metadata and repo-local workflow config.

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
