---
id: WI-UNIFIED-COMMAND-MODEL-0001
title: Adopt unified Taurworks command model
type: deliverable
status: resolved
blocked: false
blocked_reason: null
resolution: Design docs (unified_command_model.md, config_model.md) delivered and kept current; the global-resolution sequence they described was implemented through later PRs. Remaining activation work tracked in WI-ACTIVATION-CONFIG-0001.
---

# WI-UNIFIED-COMMAND-MODEL-0001: Adopt unified Taurworks command model

## Status
Resolved. The unified command model design docs are in place, and the global
resolution sequence they described (items 1-6 of the follow-up slice below)
has since been implemented, not just designed. Remaining activation work
(legacy inspect/migrate, trusted hooks) is tracked in
`WI-ACTIVATION-CONFIG-0001` rather than here.

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
- `project/design/unified_command_model.md` (kept current)
- `project/design/config_model.md` (kept current)
- Aligned updates across existing `project/` LRH documents.

## Follow-up implementation work
This work item's own scope was design/documentation alignment only. The
sequence below was implemented through later PRs and is tracked as done here
for historical continuity; ongoing activation work is `WI-ACTIVATION-CONFIG-0001`.

## Resolved follow-up slice
Dogfooding confirmed that local initialized-project activation worked after loading the sourceable helper, but also exposed a global resolution gap: initialized projects in nested locations were not reliably discoverable from a workspace root unless registered, and `tw activate NAME` was too dependent on the current directory. That gap is closed:

1. XDG-style user-global config implemented at `$XDG_CONFIG_HOME/taurworks/config.toml`, with `~/.config/taurworks/config.toml` fallback, schema version 1, and explicit `[workspace].root`. Implemented commands: `taurworks config where`, `taurworks workspace show`, and `taurworks workspace set PATH`. **Done.**
2. Global project registry implemented under `[projects.NAME]` with commands `taurworks project register NAME PATH`, `taurworks project unregister NAME`, and `taurworks project registry list`; supports intentionally weird locations without recursive scanning by default. **Done.**
3. `tw projects` / `taurworks projects` merge registered projects, immediate workspace-root children, initialized projects, legacy-admin projects, and workspace-only projects. **Done.**
4. `tw activate NAME` resolves from anywhere using the canonical priority list in `project/design/config_model.md`: registered project, initialized workspace project, legacy-admin workspace project, workspace-only directory, local/enclosing fallback, then child path only for explicitly local commands. **Done.**
5. Conservative activation semantics preserved: initialized with `working_dir` changes there; initialized without `working_dir`, workspace-only, and legacy-admin fall back to project root with warnings; legacy scripts are recognized but not sourced by default. **Done.**
6. Phase 2 declarative activation config implemented for readiness messages and `[activation.exports]` data, plus Conda as the first environment strategy, without arbitrary user-script sourcing. **Done.**
7. User scripts/hooks remain deferred to a future explicit opt-in trust model with warnings, inspection/dry-run modes, per-project trust, and a possible migration path from `Admin/project-setup.source`. **Intentionally still deferred** — tracked as slice 6 of `WI-ACTIVATION-CONFIG-0001`.
