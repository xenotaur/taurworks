---
prompt_id: "PROMPT(AD_HOC:FIX_TOP_LEVEL_TEST_LAYOUT)[2026-04-30T03:05:00-04:00]"
work_item: "AD_HOC"
slug: "fix-top-level-test-layout"
status: "landed"
date: "2026-04-30"
---

# Summary
Restructured test files to mirror current top-level modules under `src/taurworks/` and moved smoke coverage under `tests/smoke/`.

# Result
- Confirmed no prior execution record for this exact prompt ID.
- Moved smoke test from `tests/layout_smoke_test.py` to `tests/smoke/layout_smoke_test.py`.
- Removed `tests/cli_tests/` and `tests/project_tests/`.
- Added top-level module tests: `tests/cli_test.py`, `tests/manager_test.py`, and `tests/project_resolution_test.py`.
- Updated `STYLE.md` with explicit top-level module test layout and smoke test location guidance.

# Validation
- `scripts/test` passed.
- `scripts/lint` initially failed due to formatting in `tests/cli_test.py`, then passed after `scripts/format`.
- Attempted to run `scripts/prompts/record-execution`, but the script is not present in this repository.

# Follow-up
If prompt execution records must always be script-generated, add `scripts/prompts/record-execution` in a separate change.
