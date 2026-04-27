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
