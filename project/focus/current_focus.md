---
updated: 2026-05-13
basis: design_alignment
confidence: high
---

# Current Focus

Taurworks is currently focused on the **minimal project metadata model** needed to distinguish `project_root`, `working_dir`, and the activation target. Dogfooding showed the previous command slice works for safe scaffolding/discovery/printed guidance, but shell activation needs richer metadata before it can be useful.

## Active direction
1. Define `.taurworks/config.toml` schema fields for project name and relative `paths.working_dir`.
2. Add `taurworks project working-dir show` and `taurworks project working-dir set [DIR]` as the first implementation slice.
3. Extend `project create PROJECT --working-dir DIR` without duplicating refresh/scaffold logic.
4. Extend `project activate --print` to print guidance for configured `working_dir`.
5. Preserve compatibility with current command behavior while deferring shell mutation.

## In scope now
- Documentation and design alignment across `project/` artifacts for the project-root/working-directory distinction.
- Guardrails for portable relative paths and rejection/deferment of absolute working-directory paths.
- Phased roadmap clarity for working-directory commands, create integration, and activation guidance.

## Out of scope now
- More package-layout work.
- Full immediate implementation of every `taurworks dev` command.
- Automatic parent-shell mutation through `tw activate` or shell wrappers.
- Multi-repo project management.
- Breaking command renames or removals.
