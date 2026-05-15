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
Dogfooding confirmed that local initialized-project activation works after loading the sourceable helper, but also exposed a global resolution gap: initialized projects in nested locations are not reliably discoverable from a workspace root unless they are registered, and `tw activate NAME` remains too dependent on the current directory.

Design and implementation should proceed in this order:

1. Add XDG-style user-global config design for `$XDG_CONFIG_HOME/taurworks/config.toml`, with `~/.config/taurworks/config.toml` fallback, schema version 1, and explicit `[workspace].root`. Planned commands are `taurworks config where`, `taurworks workspace show`, and `taurworks workspace set PATH`.
2. Add global project registry design under `[projects.NAME]` with planned commands `taurworks project register NAME PATH`, `taurworks project unregister NAME`, and `taurworks project registry list`; support intentionally weird locations without recursive scanning by default.
3. Make `tw projects` / `taurworks projects` design merge registered projects, immediate workspace-root children, initialized projects, legacy-admin projects, and workspace-only projects.
4. Make `tw activate NAME` design resolve from anywhere using the canonical priority list in `project/design/config_model.md`: registered project, initialized workspace project, legacy-admin workspace project, workspace-only directory, local/enclosing fallback, then child path only for explicitly local commands.
5. Preserve conservative activation semantics: initialized with `working_dir` changes there; initialized without `working_dir`, workspace-only, and legacy-admin fall back to project root with warnings; legacy scripts are recognized but not sourced by default.
6. Design Phase 2 declarative activation config for readiness messages, environment strategies such as Conda/venv, and `[activation.exports]` data without arbitrary user-script sourcing.
7. Defer user scripts/hooks to a future explicit opt-in trust model with warnings, inspection/dry-run modes, per-project trust, and a possible migration path from `Admin/project-setup.source`.

This follow-up remains a design/control-plane alignment slice. It should not implement global config, registry commands, activation behavior changes, declarative activation, user-script execution, or automatic legacy setup sourcing.
