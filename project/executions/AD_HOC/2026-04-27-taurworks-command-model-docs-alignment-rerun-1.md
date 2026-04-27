---
prompt_id: "PROMPT(TAURWORKS_COMMAND_MODEL_DOCS_ALIGNMENT)[DOCS/2026-04-27]"
work_item: "AD_HOC"
slug: "taurworks-command-model-docs-alignment-rerun-1"
status: "landed"
date: "2026-04-27"
rerun_of: "project/executions/AD_HOC/2026-04-27-taurworks-command-model-docs-alignment.md"
---

# Summary
Addressed PR review feedback for README command-availability clarity and execution-record grammar.

# Result
- Added an explicit status note in README that `taurworks project ...` and `taurworks dev ...` are planned and not currently implemented in the shipped CLI.
- Corrected execution-record validation grammar from "due unavailable" to "due to unavailable".

# Validation
- Reviewed updated markdown for consistency and correctness.
- Ran CLI smoke test: `PYTHONPATH=src python -m taurworks.cli --help`.

# Follow-up
- Keep README and design docs synchronized as namespaced command implementation progresses.
