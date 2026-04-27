---
updated: 2026-04-27
basis: design_alignment
confidence: high
---

# Current Focus

Taurworks is currently focused on **design alignment and command model clarification**, not immediate implementation of every planned dev command.

## Active direction
1. Keep one primary executable: `taurworks`.
2. Clarify namespaced project lifecycle commands under `taurworks project ...`.
3. Clarify namespaced repo workflow commands under `taurworks dev ...`.
4. Keep a shared config/discovery model across both namespaces.
5. Preserve compatibility with current command behavior while a migration path is defined.

## In scope now
- Documentation and design alignment across `project/` artifacts.
- Guardrails for safety and shell integration.
- Phased roadmap clarity.

## Out of scope now
- Full immediate implementation of every `taurworks dev` command.
- Breaking command renames or removals.
