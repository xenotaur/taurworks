---
id: WI-UNIFIED-COMMAND-MODEL-0001
status: active
---

# WI-UNIFIED-COMMAND-MODEL-0001: Adopt unified Taurworks command model

## Status
In progress (design/documentation alignment)

## Objective
Align `project/` control-plane documentation to a unified Taurworks command model based on one executable (`taurworks`) with separate `project` and `dev` namespaces.

## Scope for this work item
- Update project goal, design overview, principles, roadmap, focus, status, guardrails, and decision log for unified command direction.
- Add canonical design notes for command model and config/state model.
- Preserve existing top-level commands as compatibility commands.

## Explicitly out of scope for this item
- Full CLI implementation redesign.
- Removing or renaming existing commands.
- Introducing plugin framework or broad adapter architecture.

## Deliverables
- `project/design/unified_command_model.md`
- `project/design/config_model.md`
- Aligned updates across existing `project/` LRH documents.

## Follow-up implementation work
Implementation remains future work and should proceed in small, reviewable phases after design alignment is agreed.

## Current follow-up slice
Dogfooding the implemented project command slice showed that the `project_root` / `working_dir` model is useful, but the lifecycle command semantics need refinement before activation can be useful. The next work should keep `project_root` as the directory containing `.taurworks/` and `working_dir` as the default code/work directory stored relative to that root, while resolving dogfood findings around target resolution and explicit creation behavior.

Implementation should proceed in this order:

1. Add `taurworks project init [PATH] [--working-dir DIR] [--create-working-dir]` for safe, idempotent initialization of existing/current project roots, reusing refresh/config logic.
2. Refine `taurworks project create NAME [--working-dir DIR] [--create-working-dir] [--nested]` so it creates a new root, delegates to init/refresh, and refuses accidental nested same-name creation unless `--nested` is supplied.
3. Centralize shared target resolution with diagnostics for no input, existing paths, current project-name input, current-directory basename input, and child-path fallback.
4. Extend `taurworks project working-dir show [PATH_OR_NAME]`, prefer `taurworks project working-dir set DIR --project PATH_OR_NAME`, and require explicit opt-in before creating missing working directories.
5. Keep `taurworks project activate [PATH_OR_NAME] --print` read-only while making it use the shared resolver and configured `working_dir`.

This follow-up remains narrower than full `taurworks dev ...`, automatic shell mutation, or multi-repo project management. It should be completed before adding `tw activate` or any shell wrapper that mutates the user shell.
