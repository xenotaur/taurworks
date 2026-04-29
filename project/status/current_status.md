# Current Status

## Maturity snapshot
Taurworks is in a design-alignment phase moving toward a unified command model while preserving current behavior.

## Current direction (documented)
- One primary executable: `taurworks`.
- Namespaced workspace lifecycle commands: `taurworks project ...`.
- Namespaced repo workflow commands: `taurworks dev ...`.
- Shared discovery/configuration core across namespaces.
- Compatibility coverage for existing top-level commands (`create`, `refresh`, `activate`, `projects`).

## Implemented minimal project slice (read-only)
- `taurworks project --help` documents the project namespace and available discovery commands.
- `taurworks project where` provides read-only project/config/discovery diagnostics.
- `taurworks project list` provides read-only discovery listing and clear no-project behavior.

## What this phase prioritizes
- Aligning design, principles, guardrails, roadmap, and decision memory.
- Clarifying command responsibilities and configuration precedence.
- Defining conservative sequencing for future implementation.

## What remains future implementation work
- Full command implementation across all `taurworks dev` verbs.
- Finalized migration/deprecation mechanics for compatibility commands.
- Expanded diagnostics and dry-run support across all command paths.
