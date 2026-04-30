---
prompt_id: "PROMPT(AD_HOC:ALIGN_TEST_TREE_LAYOUT)[2026-04-30T02:10:00-04:00]"
work_item: "AD_HOC"
slug: "align-test-tree-layout"
status: "landed"
date: "2026-04-30"
---

# Summary
Restructured the test tree to mirror `src/taurworks/` module ownership per `STYLE.md` test layout rules.

# Result
- Confirmed no prior execution record existed for this prompt ID.
- Moved project command tests from `tests/project_tests/` into `tests/cli_tests/`.
- Renamed `project_list_test.py` to `cli_test.py` under `tests/cli_tests/`.
- Updated helper imports from `tests.project_tests` to `tests.cli_tests` in moved test modules.
- Preserved `tests/layout_smoke_test.py` as a cross-cutting smoke test.
- Removed empty legacy `tests/project_tests/` directory.

# Validation
- Ran `scripts/test` (pass).
- Ran `scripts/lint` (pass).
- Attempted `scripts/prompts/record-execution` per prompt guidance, but script is not present in this repository.

# Follow-up
If prompt bookkeeping should be scripted, add `scripts/prompts/record-execution` and the referenced `project/executions/README.md` in a separate change.
