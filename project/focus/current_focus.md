---
updated: 2026-05-13
basis: design_alignment
confidence: high
---

# Current Focus

Taurworks is currently focused on the **dogfood-resolution design** for project lifecycle commands. The `project_root` / `working_dir` metadata model remains correct, but dogfooding showed that Taurworks must clarify initialization versus creation, centralize target resolution, make missing working-directory creation explicit, and prevent accidental nested same-name projects before adding shell mutation.

## Active direction
1. Add `taurworks project init [PATH] [--working-dir DIR] [--create-working-dir]` for safe, idempotent initialization of an existing/current root while reusing refresh/config logic.
2. Refine `taurworks project create NAME [--working-dir DIR] [--create-working-dir] [--nested]` so it creates a new project root, delegates to init/refresh, and refuses accidental nested same-name creation unless `--nested` is supplied.
3. Centralize shared project target resolution and make command output diagnostic, including `input`, selected `project_root`, and `resolved_by`.
4. Make `taurworks project working-dir show [PATH_OR_NAME]` target-aware and prefer `taurworks project working-dir set DIR --project PATH_OR_NAME` over ambiguous positional overloads.
5. Require explicit opt-in to create missing working directories through `--create-working-dir` or `working-dir set --create`.
6. Keep `taurworks project activate [PATH_OR_NAME] --print` read-only and resolver-backed.
7. Preserve compatibility with current command behavior while deferring shell mutation.

## In scope now
- Documentation and design alignment across `project/` artifacts for the accepted init/create/resolver design.
- Guardrails for portable relative paths and rejection/deferment of absolute working-directory paths.
- Guardrails for explicit missing working-directory creation and accidental nested same-name project creation.
- Phased roadmap clarity that this sequence addresses dogfood findings and should land before `tw activate` or any shell wrapper that mutates the user shell.

## Out of scope now
- Implementing `project init`, resolver behavior changes, create behavior changes, or activation behavior changes in this documentation PR.
- More package-layout work.
- Full immediate implementation of every `taurworks dev` command.
- Automatic parent-shell mutation through `tw activate` or shell wrappers.
- Multi-repo project management.
- Breaking command renames or removals.
