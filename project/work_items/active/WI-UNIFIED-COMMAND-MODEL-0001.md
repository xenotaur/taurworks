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
Dogfooding confirmed that the first shell activation path works: `tw project create TestProject --working-dir test_repo --create-working-dir` followed by `tw activate TestProject` changes into the configured working directory, and missing project activation fails safely.

Implementation should proceed in this order:

1. Polish `tw activate` output so defaults are concise, detailed activation diagnostics require `--verbose` or `--debug`, missing project/working-directory cases print concise warnings by default, `tw help` aliases `tw --help`, and successful activation behavior remains unchanged.
2. Classify `tw projects` / `taurworks projects` results as initialized projects with `.taurworks/config.toml`, workspace-only directories, or legacy-admin directories with `Admin/project-setup.source`.
3. Keep activation support limited to initialized projects for now. Do not add legacy-admin fallback sourcing as default behavior; leave old setup scripts for future explicit migration.
4. Add a minimal read-only `taurworks dev ...` namespace scaffold with safe diagnostics such as `dev where` and/or `dev status`.
5. Design activation extensions for readiness messages, environment activation strategies, trusted per-project startup hooks, legacy `Admin/project-setup.source` migration, and trust/safety boundaries.

This follow-up remains narrower than full `taurworks dev ...` automation, shell startup-file edits, multi-repo project management, or automatic sourcing of legacy project setup scripts. Automatic legacy sourcing is intentionally deferred because it crosses a stronger trust boundary than `cd`-only activation.
