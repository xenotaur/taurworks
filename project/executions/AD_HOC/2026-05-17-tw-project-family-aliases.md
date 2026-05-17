---
prompt_id: "PROMPT(AD_HOC:tw-project-family-aliases)[20260517T000721Z]"
work_item: "AD_HOC"
slug: "tw-project-family-aliases"
status: "landed"
date: "2026-05-17"
---

# Summary
Implemented the prompt-driven `tw project` path-emitter family and short aliases for shell composition.

# Result
- Added `taurworks project root PROJECT` and `taurworks project working PROJECT` as explicit path emitters that print one absolute path on success.
- Added top-level `taurworks root PROJECT` and `taurworks working PROJECT` aliases; the sourced `tw` helper delegates these as `tw root PROJECT` and `tw working PROJECT`.
- Reused global registry/workspace/current project resolution for path emitters and kept diagnostics on stderr for failures.
- Updated README and control-plane status/roadmap notes for the new user-facing command capability.
- Added CLI tests for root/working emitters, aliases, stdout/stderr shape, unknown project failures, paths with spaces, and continuing activation guidance behavior.

# Validation
- Passed `scripts/format --check`.
- Passed `scripts/lint`.
- Passed `scripts/test`.
- Attempted `scripts/prompts/record-execution --help` before creating this record; it failed because `scripts/prompts/record-execution` is not present in this repository checkout, so this record was created manually following `project/executions/README.md`.

# Follow-up
None.
