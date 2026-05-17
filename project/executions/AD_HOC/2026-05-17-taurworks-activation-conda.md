---
prompt_id: "PROMPT(TAURWORKS_ACTIVATION_CONDA)[IMPLEMENT/2026-05-16]"
work_item: "AD_HOC"
slug: "taurworks-activation-conda"
status: "landed"
date: "2026-05-17"
---

# Summary
Implemented Conda support for declarative Taurworks activation config.

# Result
- Added validated `[activation.environment]` parsing for `type = "conda"` and a required conservative Conda environment `name`.
- Updated read-only `taurworks project activate --print` diagnostics to report environment configuration without mutating shell state.
- Updated the sourced `tw activate` helper to run `conda activate <name>` when configured, apply exports only after environment activation succeeds, then change directory and print activation messages.
- Documented the Conda activation schema, requirements, ordering, and deferred environment/hook types.
- Added unit and shell-helper tests for read-only reporting, invalid environment config, successful fake Conda activation, failure handling without leaked exports, and no-Conda behavior when no environment is configured.

# Validation
- Passed: `./scripts/test`
- Passed: `./scripts/lint`
- Passed: `./scripts/format --check --diff`
- Passed: controlled fake Conda shell validation with `python -m pip install -e . --no-build-isolation`, temporary `XDG_CONFIG_HOME`, `taurworks workspace set`, `taurworks project create`, a fake `conda` shell function, `taurworks shell print`, and `tw activate Alpha`.
- Note: `scripts/prompts/record-execution` was unavailable in this checkout, so this execution record was created manually following `project/executions/README.md`.

# Follow-up
None.
