---
prompt_id: "PROMPT(TAURWORKS_GLOBAL_RESOLUTION_ACTIVATE_PROJECTS)[IMPLEMENT/2026-05-15]"
work_item: "AD_HOC"
slug: "taurworks-global-resolution-activate-projects"
status: "landed"
date: "2026-05-16"
---

# Summary
Implemented global workspace/registry-aware project listing and activation resolution for `taurworks projects`, `tw projects`, `taurworks project activate --print`, and sourced-shell `tw activate`.

# Result
- Added global-first activation resolution: registry name, configured workspace direct children by initialized/legacy/workspace-only status, current-project fallback, and explicit local path inputs.
- Updated activation guidance and the shell helper so initialized projects without `working_dir`, workspace-only projects, and legacy-admin projects change to the project root with warnings instead of sourcing scripts or running environment activation.
- Updated project listing to include configured workspace children and registered roots, collapse duplicate roots, and display source/registered status.
- Documented the new behavior and noted that `project create NAME` remains cwd-relative in this focused change.
- Added and updated tests for global activation/listing, registry-hidden projects, duplicate suppression, non-recursive workspace listing, shell warnings, and updated activation semantics.

# Validation
- Passed: `./scripts/format`.
- Passed: `./scripts/test`.
- Passed: `./scripts/lint`.
- Warning: `python -m pip install -e .` failed because build isolation attempted to download `setuptools>=64` and the environment returned a 403 from the package index.
- Passed with environment workaround: `python -m pip install -e . --no-build-isolation`.
- Passed end-to-end temporary workspace flow for `taurworks workspace set`, `taurworks project init`, `taurworks projects`, and `taurworks project activate ... --print` for initialized, workspace-only, and legacy-admin projects.
- Passed sourced shell helper flow for `tw activate TaurworksLike`, `tw activate WorkspaceOnly`, and `tw activate Legacy`.
- Warning: `scripts/prompts/record-execution` is not present in this checkout; this record was created manually following `PROMPTS.md` and `project/executions/README.md`.

# Follow-up
- Consider a separate focused design/implementation for making `project create NAME` default to the configured workspace root with explicit `--local`, `--path PATH`, or `--register` controls.
