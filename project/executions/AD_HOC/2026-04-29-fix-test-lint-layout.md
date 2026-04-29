---
prompt_id: "PROMPT(AD_HOC:FIX_TEST_LINT_LAYOUT)[2026-04-28T14:20:00-04:00]"
work_item: "AD_HOC"
slug: "fix-test-lint-layout"
status: "landed"
date: "2026-04-29"
---

# Summary
Validated the repository against the canonical test/lint/format scripts and resolved the active lint failure.

# Result
- Confirmed there were no existing execution records for this exact prompt ID.
- Ran canonical scripts and found tests passing but lint failing due to Black formatting in `src/taurworks/manager.py`.
- Applied Black-compatible formatting in `src/taurworks/manager.py` (multiline `f.write(...)` blocks).
- Re-ran test/lint/format checks; all passed.
- No test layout moves were needed because the current `tests/*_tests/*_test.py` structure already matches `STYLE.md`.

# Validation
- Ran `scripts/develop`.
- Ran `scripts/test`.
- Ran `scripts/lint` (initially failed; Black wanted to reformat `src/taurworks/manager.py`).
- Ran `scripts/format --check` (command executes formatter in this repository and reformatted `src/taurworks/manager.py`).
- Re-ran `scripts/test` (pass).
- Re-ran `scripts/lint` (pass).
- Re-ran `scripts/format --check` (no additional changes).
- Attempted `scripts/prompts/record-execution --help` (script missing in repository).

# Follow-up
- Add `project/executions/README.md` and `scripts/prompts/record-execution` if this prompt workflow is expected to be mandatory in this repository state.
